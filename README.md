##How to compile 

mkdir -p build
cd build
cmake ..
make

# im Repo-Root
python3 -m venv .venv
source .venv/bin/activate

python3 -m pip install -U pip setuptools wheel
python3 -m pip install pybind11 cmake   

# alte Artefakte löschen (falls vorhanden)
rm -rf build/ *.egg-info **/*.so

# jetzt wirklich bauen & installieren – mit Verbose
pip3 install -e ".[app,test]" -v
