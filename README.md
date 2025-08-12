# MCMC Simulator Dashboard

Interactive Monte Carlo simulations (Ising, Clock, XY) in browser – powered by a C++ core, Python pipelines, a Streamlit frontend, and a Supabase database.

**🎯 Live Demo:** [Click here to launch the app](<https://a9hrzvqsl5gvz5ps7btra7.streamlit.app>)

---

## 🚀 Features

- **Three models**: Ising, Clock, XY  
- **Configurable parameters** directly in the app:
  - Lattice size L
  - Temperature range & step size
  - Number of MCMC steps
- **Visualization**:
  - GIF animations of spin evolution
  - Error bar plots for energy, magnetization, heat capacity, and susceptibility
- **Supabase integration**:
  - Stores simulations, lattices, and statistics
  - Retrieve and explore previous runs
- **Cloud-based**:
  - No installation required
  - Runs entirely in the browser

---

## 📖 How to Use

1. **Open the app**  
   [<Click here to open the app>](<https://a9hrzvqsl5gvz5ps7btra7.streamlit.app>)

2. **Configure the simulation**  
   - Choose model, lattice size, temperatures, and steps

3. **Run the simulation**  
   - A progress bar shows the status  
   - Results are automatically displayed in the app

4. **Analyze & export**  
   - View GIF animations and plots directly in the app  

---

- C++ core: Efficient update kernels for Ising, Clock, and XY models
- Python pipeline: Statistical analysis, visualization, and export
- Streamlit frontend: Interactive configuration and display
. Supabase (Postgres): Persistent storage of all simulation results

## 📌 Tech Stack

- **Core**: C++17, pybind11  
- **Frontend**: Streamlit  
- **Backend**: Python, NumPy, Plotly, SQLAlchemy  
- **Database**: Supabase (Postgres)  
- **CI/CD**: GitHub Actions (build, test)


# 1) Clone the repository
git clone https://github.com/<your-user>/<repo>.git
cd <repo>

# 2) Create a virtual environment
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# 3) Install dependencies
pip install -r requirements.txt

# 4) Install mcmc_tools (if in repo)
pip install -e ./mcmc_tools

# 5) Build the C++ core
mkdir -p build && cd build
cmake -DPython3_EXECUTABLE="$(which python)" -DCMAKE_BUILD_TYPE=Release ..
make -j
cd ..
export PYTHONPATH="$PWD/build:$PWD"

# 6) Set environment variables
export DATABASE_URL="postgresql+psycopg2://<user>:<pass>@<host>:<port>/<db>"
export SAFE_MODE="1"

# 7) Run the app
streamlit run app.py
