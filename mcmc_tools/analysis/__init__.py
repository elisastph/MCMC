# Erstellt ALLE Tabellen basierend auf den ORM-Klassen
from mcmc_tools.db.connection import engine
from mcmc_tools.db.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("✅ Tabellen wurden erstellt.")
