from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func

Base = declarative_base()

class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True)
    model = Column(String)
    temperature = Column(Float)
    steps = Column(Integer)
    lattice_size = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"))
    step = Column(Integer)
    energy = Column(Float)
    magnetization = Column(Float)
    energy_squared = Column(Float)
    magnetization_squared = Column(Float)

class Plot(Base):
    __tablename__ = "plots"
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"))
    step = Column(Integer)
    path = Column(String)
    type = Column(String)  # z.B. 'lattice'

class Statistic(Base):
    __tablename__ = "statistics"
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"))
    temperature = Column(Float)
    energy_per_spin = Column(Float)
    magnetization_per_spin = Column(Float)
    heat_capacity = Column(Float)
    susceptibility = Column(Float)
    error_energy = Column(Float)
    error_magnetization = Column(Float)
    error_cv = Column(Float)
    error_chi = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Lattice(Base):
    __tablename__ = "lattices"
    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"))
    model = Column(String)
    temperature = Column(Float)
    step = Column(Integer)
    data = Column(Text)  # z.B. Base64-encoded NumPy array
