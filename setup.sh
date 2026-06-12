#/bin/bash


# Stop script on errors:
set -e


# Check environment:
if ! command -v pip >/dev/null 2>&1; then
	echo "[ERROR] Missing 'pip' on your system. For Ubuntu/Debian run: sudo apt install python3-pip" >&2
	exit 1
fi


# Change to project directory:
pushd "$(dirname "$(realpath "$0")")" > /dev/null || exit 1


# Base:
mkdir -p routes
chmod u+x *.sh *.py


# Install dependencies in local project directory:
python -m venv "local"
source "local/bin/activate"
# Indirect deps:
#    shapely <- geopandas
#    pandas  <- geopandas
pip install gpxpy shapely pyproj simplekml



popd > /dev/null || exit 1


