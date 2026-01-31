# step-02

## Requirements Overview (Brownfield Reality)

### Functional Requirements

#### Semantic Book Search
**all-MiniLM-L6-v2** je dobro izabran model? postoje puno jači modeli s više dimenzija. još smo u fazi testiranja, još možemo mijenjat model. 

## Scale & Complexity Assessment

### Project Complexity

- No authentication. MCP treba nešto znati o autentikaciji?

### Cross-Cutting Concerns

- opsežan logging u sqlite bazu? kada, od kuda, što ...
- progress tracking obavezno. streamlit ne mora znati ništa o tome?

# Technical Constraints & Dependencies

## Hard Constraints (Cannot Change)
  1. razmisliti o modelu, da li postoji model koji daje bitno bolje razultate za prihvatljiv trošak

