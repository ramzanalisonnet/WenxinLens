# Advanced Feature Layer

## Overview

WenxinLens now includes a research-grade advanced feature layer integrated into the orchestrator.

Pipeline:

Recognition Agent -> Retrieval Agent -> Advanced Feature Agents -> Explanation Agent -> Interaction Agent

Implemented advanced agents:

- TimeReconstructionAgent
- HistoricalCharacterAgent
- CulturalDNAAgent
- ComparisonAgent
- CinematicAgent

## Backend Modules

Agent modules:

- backend/agents/time_reconstruction_agent/agent.py
- backend/agents/historical_character_agent/agent.py
- backend/agents/cultural_dna_agent/agent.py
- backend/agents/comparison_agent/agent.py
- backend/agents/cinematic_agent/agent.py

Shared feature service:

- backend/services/advanced_feature_service.py

Orchestrator integration:

- backend/agents/orchestrator.py

API routes:

- backend/api/routes/advanced.py

## API Contracts

### POST /api/v1/advanced/all

Request payload:

- building_name: string
- dynasty: string
- architecture_style: string
- structural_features: string[]
- language: en | zh
- user_message: string

Response payload includes:

- time_reconstruction
- historical_character
- cultural_dna
- cross_civilization
- cinematic_story
- summary

### POST /api/v1/advanced/historical-character

Request payload:

- building_name: string
- dynasty: string
- character_type: emperor | architect | worker | scholar
- message: string
- language: en | zh

Response payload:

- character
- persona_name
- reply
- grounding_sources

## Grounding and Explainability

All advanced feature methods use retrieval_service.search and retrieval_service.format_context for factual grounding.

Each feature payload includes grounding_sources to expose source provenance.

## Performance and Scalability

- Advanced features are executed concurrently in orchestrator._run_advanced_layer using asyncio.gather.
- Redis cache is used in advanced_feature_service for expensive outputs.
- Config includes GPU diffusion toggles and model settings for production image generation integration.

## Frontend Integration

Route:

- /lab

Page:

- frontend/src/app/lab/page.tsx

UI modules:

- TimeReconstructionView
- HistoricalCharacterChat
- CulturalDnaDashboard
- ComparisonPanel
- CinematicStoryMode

API client:

- frontend/src/services/api.ts -> advancedApi

Types:

- frontend/src/types/index.ts

## Deployment Notes

Docker Compose and Kubernetes manifests include advanced feature environment knobs:

- ENABLE_GPU_DIFFUSION
- TIME_RECONSTRUCTION_MODEL
- TIME_RECONSTRUCTION_CONTROLNET
- ADVANCED_FEATURE_CACHE_TTL_SECONDS

For production, connect a real diffusion worker service and object storage for generated assets.
