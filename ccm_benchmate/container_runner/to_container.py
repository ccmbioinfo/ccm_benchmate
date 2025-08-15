import os
import subprocess
import argparse
import sys
import yaml
from urllib.parse import urlparse
import docker
from docker.errors import DockerException, APIError, BuildError
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments with clear descriptions and validation."""
    parser = argparse.ArgumentParser(
        description="Create and manage a Docker container with a Conda environment, cloned Git repository, and script execution, compatible with Apptainer."
    )
    parser.add_argument('--env-yaml', required=True, type=str,
                        help="Path to the Conda environment.yaml file")
    parser.add_argument('--git-repo', required=True, type=str,
                        help="URL of the Git repository to clone (e.g., https://github.com/user/repo.git)")
    parser.add_argument('--scripts', nargs='+', required=True, type=str,
                        help="List of script paths to copy and run in order")
    parser.add_argument('--build-image', action='store_true',
                        help="Build the Docker image if specified")
    parser.add_argument('--push-registry', default=None, type=str,
                        help="Registry to push the Docker image (e.g., docker.io/username/repo:tag)")
    parser.add_argument('--create-sif', action='store_true',
                        help="Create an Apptainer .sif file after pushing to registry or building locally")
    parser.add_argument('--image-name', default='custom-conda-env', type=str,
                        help="Name of the Docker image (default: custom-conda-env)")
    parser.add_argument('--tag', default='latest', type=str,
                        help="Tag for the Docker image (default: latest)")
    return parser.parse_args()


def read_yaml(file_path):
    """Read and parse a YAML file, raising errors for handling."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    with file_path.open('r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {file_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error reading YAML file {file_path}: {e}")


def get_repo_name(git_url):
    """Extract repository name from Git URL, raising errors for handling."""
    parsed_url = urlparse(git_url)
    if not parsed_url.scheme or not parsed_url.path:
        raise ValueError(f"Invalid Git URL: {git_url}")
    repo_name = os.path.basename(parsed_url.path).replace('.git', '')
    return repo_name


def create_dockerfile(conda_env_name, git_repo, scripts):
    """Generate a Dockerfile optimized for Apptainer compatibility."""
    script_commands = []
    for script in scripts:
        script_name = os.path.basename(script)
        script_commands.append(f"/app/scripts/{script_name}")

    dockerfile_content = f"""
FROM continuumio/miniconda3:latest

# Install system dependencies for GPU support, Git, and Apptainer compatibility
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    build-essential \\
    libgl1-mesa-glx \\
    libegl1-mesa \\
    libxrandr2 \\
    libxss1 \\
    libxcursor1 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxi6 \\
    libxtst6 \\
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and create Conda environment
COPY environment.yaml /tmp/environment.yaml
RUN conda env create -f /tmp/environment.yaml && \\
    conda clean --all -f -y && \\
    rm /tmp/environment.yaml

# Activate Conda environment
ENV PATH=/opt/conda/envs/{conda_env_name}/bin:$PATH
SHELL ["/bin/bash", "-c"]
RUN echo "source activate {conda_env_name}" > ~/.bashrc

# Ensure Apptainer compatibility: writable /tmp, /var/tmp, and basic permissions
RUN mkdir -p /tmp /var/tmp /app && \\
    chmod -R 777 /tmp /var/tmp /app

# Clone the Git repository
ARG GIT_REPO={git_repo}
RUN git clone "$GIT_REPO" /app/repo && \\
    if [ ! -d "/app/repo" ]; then exit 1; fi

# Set working directory
WORKDIR /app/repo

# Copy and make scripts executable
COPY scripts/ /app/scripts/
RUN chmod +x /app/scripts/*

# Run scripts in order
CMD {' && '.join([f'/bin/bash -c "source activate {conda_env_name} && /app/scripts/{os.path.basename(script)}"' for script in scripts])}
"""
    with open('Dockerfile', 'w') as f:
        try:
            f.write(dockerfile_content)
            logger.info("Dockerfile created successfully")
            return dockerfile_content
        except IOError as e:
            raise IOError(f"Error writing Dockerfile: {e}")


def copy_scripts(scripts):
    """Copy scripts to a temporary directory with validation."""
    script_dir = Path('scripts')
    script_dir.mkdir(exist_ok=True)
    for script in scripts:
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script}")
        shutil.copy(script_path, script_dir / script_path.name)
    logger.info("Scripts copied successfully")


def build_docker_image(image_name, tag):
    """Build a Docker image with detailed error handling."""
    client = docker.from_env()
    logger.info(f"Building Docker image: {image_name}:{tag}")
    image, build_logs = client.images.build(path='.', tag=f"{image_name}:{tag}", rm=True)
    for line in build_logs:
        if 'stream' in line:
            logger.info(line['stream'].strip())
    logger.info(f"Successfully built {image_name}:{tag}")
    return image


def push_to_registry(image_name, tag, registry):
    """Push the Docker image to a specified registry."""
    client = docker.from_env()
    full_image = f"{registry}" if registry else f"{image_name}:{tag}"
    image = client.images.get(f"{image_name}:{tag}")
    if registry:
        image.tag(full_image)
    logger.info(f"Pushing image to registry: {full_image}")
    for line in client.images.push(full_image, stream=True, decode=True):
        if 'status' in line:
            logger.info(line['status'])
        if 'error' in line:
            raise RuntimeError(f"Push error: {line['error']}")
    logger.info(f"Successfully pushed {full_image}")


def create_apptainer_sif(image_name, tag, registry):
    """Create an Apptainer .sif file from the Docker image."""
    full_image = f"{registry}" if registry else f"{image_name}:{tag}"
    sif_file = f"{image_name}_{tag}.sif"
    logger.info(f"Creating Apptainer .sif file from {full_image}")
    result = subprocess.run(['apptainer', 'build', sif_file, f"docker://{full_image}"],
                            check=True, capture_output=True, text=True)
    logger.info(f"Successfully created {sif_file}")


def cleanup():
    """Clean up temporary files and directories."""
    try:
        if Path('Dockerfile').exists():
            Path('Dockerfile').unlink()
            logger.info("Cleaned up Dockerfile")
        if Path('scripts').exists():
            shutil.rmtree('scripts')
            logger.info("Cleaned up scripts directory")
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")



if __name__ == "__main__":
    args = parse_args()
    try:
        try:
            # Read Conda environment YAML
            env_config = read_yaml(args.env_yaml)
            conda_env_name = env_config.get('name', 'myenv')
            logger.info(f"Conda environment name: {conda_env_name}")

            # Get repository name from Git URL
            repo_name = get_repo_name(args.git_repo)
            logger.info(f"Repository name: {repo_name}")

            # Copy scripts to a temporary directory
            copy_scripts(args.scripts)

            # Create Dockerfile with Apptainer compatibility
            create_dockerfile(conda_env_name, args.git_repo, args.scripts)

            # Build Docker image if requested
            full_image_name = f"{args.image_name}:{args.tag}"
            if args.build_image:
                try:
                    build_docker_image(args.image_name, args.tag)
                except (BuildError, APIError, DockerException) as e:
                    raise RuntimeError(f"Failed to build Docker image: {e}")

                # Push to registry if specified
                if args.push_registry:
                    try:
                        push_to_registry(args.image_name, args.tag, args.push_registry)
                    except (APIError, DockerException) as e:
                        raise RuntimeError(f"Failed to push to registry: {e}")

                    # Create Apptainer .sif file if requested
                    if args.create_sif:
                        try:
                            create_apptainer_sif(args.image_name, args.tag, args.push_registry)
                        except subprocess.CalledProcessError as e:
                            raise RuntimeError(f"Error creating Apptainer .sif file: {e.stderr}")
                        except FileNotFoundError:
                            raise RuntimeError("Apptainer not found. Ensure 'apptainer' is installed and in PATH.")
                # Create Apptainer .sif file locally if requested and not pushed
                elif args.create_sif:
                    try:
                        create_apptainer_sif(args.image_name, args.tag, None)
                    except subprocess.CalledProcessError as e:
                        raise RuntimeError(f"Error creating Apptainer .sif file: {e.stderr}")
                    except FileNotFoundError:
                        raise RuntimeError("Apptainer not found. Ensure 'apptainer' is installed and in PATH.")

        except Exception as e:
            logger.error(f"Error: {e}")
            raise  # Re-raise to ensure finally block runs
        finally:
            cleanup()
    except Exception as e:
        logger.error(f"Program terminated due to error: {e}")
        sys.exit(1)