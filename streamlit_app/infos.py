import streamlit as st 

def render_models_intro():
    st.header("What are we simulating?")
    st.write(
        "Here’s a quick, plain-language introduction to the **Ising**, **Clock**, and **XY** models, "
        "and what the controls (L, Steps, Temperature) mean."
    )

    col1, col2, col3 = st.columns(3)

    # --- Ising ---
    with col1:
        st.subheader("Ising model")
        st.markdown(
            "Each point (spin) can only be **up** (+1) or **down** (−1). "
            "Neighboring spins prefer to be in the same state.\n\n"
            "**Energy formula:**"
        )
        st.latex(r"\mathcal{H} = -J \sum_{\langle i,j\rangle} s_i s_j")
        st.markdown(
            "- **Low $T$**: most spins point the same way.\n"
            "- **High $T$**: spins are random.\n"
            "- In 2D, the change happens at about $T_c \\approx 2.27$ (in units of $J/k_B$)."
        )

    # --- Clock ---
    with col2:
        st.subheader("Clock model")
        st.markdown(
            "Each spin can point in one of **M fixed directions** (like hours on a clock). "
            "This is a step between Ising (2 directions) and XY (infinite directions).\n\n"
            "**Energy formula:**"
        )
        st.latex(r"\mathcal{H} = -J \sum_{\langle i,j\rangle} \cos(\theta_i - \theta_j)")
        st.markdown(
            "- **Low $T$**: spins choose one of the preferred directions.\n"
            "- **High $T$**: spins point in all directions equally."
        )

    # --- XY ---
    with col3:
        st.subheader("XY model")
        st.markdown(
            "Each spin can point in **any** direction between 0° and 360°.\n\n"
            "**Energy formula:**"
        )
        st.latex(r"\mathcal{H} = -J \sum_{\langle i,j\rangle} \cos(\theta_i - \theta_j)")
        st.markdown(
            "- **Low $T$**: spins tend to align locally, forming smooth patterns.\n"
            "- **High $T$**: spins are disordered; in 2D this is not a sharp phase change but a more subtle effect (BKT transition)."
        )

    st.markdown("---")
    st.subheader("About MCMC")
    st.markdown(
        "We use **Markov Chain Monte Carlo (MCMC)** to let the system evolve step by step.\n"
        "- In each step, we try small random changes to the spins or angles.\n"
        "- Changes that lower the energy are accepted, and sometimes we accept worse states to mimic thermal motion.\n"
        "- At low temperature, flips are rare, so you may see little change unless you run many steps."
    )

    st.markdown("---")
    st.subheader("About the controls")
    st.markdown(
        "- **Grid size $L$**: Creates an $L \\times L$ grid. Bigger grids → smoother results, but slower.\n"
        "- **MCMC Steps**: Number of Monte Carlo measurements per temperature. More steps → more reliable averages.\n"
        "- **Temperature $T$**: Low $T$ makes spins align; high $T$ makes them random."
    )
    st.info(
        "Tip: Start small (e.g., L=16, 10k steps), explore several temperatures, then increase L for better resolution."
    )

def render_analysis_intro():
    st.header("What happens after a run?")
    st.markdown(
        "You can **watch animations** showing how the spins change at a fixed temperature, "
        "or **plot average quantities** (with error bars) to see where changes happen."
    )

def render_gif_snippet():
    with st.expander("🎬 Evolution GIFs — what to look for", expanded=True):
        st.markdown(
            "- **Ising**: At low $T$, you will mostly observe aligned spins. "
            "Near the critical $T$, clusters appear and disappear quickly.\n"
            "- **XY**: In the XY model, each site points like a tiny arrow. At low T, most arrows point the same way. At higher T, swirling patterns called vortices appear more often.\n"
            "- **Clock**: Like XY, but with fixed directions; patches of similar angles appear.\n\n"
            "**Why you may see no flips at low $T$:**\n"
            "The system starts in an ordered state and the temperature is too low to make flips likely. "
            "With few accepted flips, the animation can look frozen. "
            "To see more motion, raise $T$ or increase the number of MCMC steps."
        )

def render_plot_snippet():
    with st.expander("📈 Plots with error bars — what they mean", expanded=True):
        st.markdown(
            "We calculate four main quantities for each temperature:\n\n"
            "- **Energy per spin** $e = \\langle E \\rangle / N$\n"
            "- **Magnetization per spin** $m = \\langle | \\text{total spin} | \\rangle / N$\n"
            "- **Heat capacity**"
        )
        st.latex(r"C_v = \frac{\langle E^2\rangle - \langle E\rangle^2}{N\,T^2}")
        st.markdown("- **Susceptibility**")
        st.latex(r"\chi = \frac{\langle M^2\rangle - \langle M\rangle^2}{N\,T}")
        st.markdown(
            "**Interpreting the plots:**\n"
            "- Sharp peaks in $C_v$ or $\\chi$ often mark a phase transition.\n"
            "- $m$ is large when spins are ordered, near zero when disordered.\n"
            "- Increasing $L$ usually makes peaks sharper."
        )
        st.info(
            "If your low-$T$ magnetization stays near 1 and nothing changes in the animation, "
            "that’s normal — the system is frozen in an ordered state. "
            "Longer runs or higher $T$ are needed to see more flips."
        )
