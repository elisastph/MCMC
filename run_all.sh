#!/bin/bash

MODELS=("Ising" "Clock" "XY")
TEMPS=$(seq 0.5 0.25 3.5) 
L=60
STEPS=100000

for MODEL in "${MODELS[@]}"; do
  for T in $TEMPS; do
    echo "Running $MODEL at T=$T..."
    build/mcmc --model $MODEL --L $L --T $T --steps $STEPS
  done
done
