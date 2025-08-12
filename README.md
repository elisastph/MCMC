# MCMC Simulator Dashboard

Interactive Monte Carlo simulations (Ising, Clock, XY) in your browser – powered by a C++ core, Python pipelines, a Streamlit frontend, and a Supabase database.

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

## 🛠 Architecture Overview

```mermaid
flowchart LR
    subgraph User
    A[Browser] -->|Streamlit UI| B[Streamlit Server]
    end

    subgraph Backend
    B -->|Parameters| C[C++ Core via pybind11]
    C -->|Raw Data| D[Python Analysis Pipeline]
    end

    D -->|Results| E[Supabase DB]
    E -->|Plots/GIFs| B

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
