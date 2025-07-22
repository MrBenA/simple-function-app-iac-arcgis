# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this Azure Function App project with ArcGIS integration.

## Project Documentation Structure

**IMPORTANT:** Always start by reading README.md for project context, current status, and high-level architecture overview.

## Available Documentation Files

### Core Documentation
- **README.md** - Start here for project overview, current status, and management tracking
- **architecture.md** - Technical architecture, tech stack, standards, and design decisions
- **data-schema.md** - Complete sensor data schema and ArcGIS field mappings

### Feature-Specific Documentation
- **app-sensor-ingestion.md** - REST API sensor data ingestion with validation
- **app-arcgis-integration.md** - ArcGIS Online connectivity and feature service operations  
- **app-data-queries.md** - Historical data retrieval and filtering endpoints
- **app-health-monitoring.md** - Health checks and system validation
- **app-infrastructure-deployment.md** - Bicep templates and GitHub Actions CI/CD

## Development Workflow

1. **Start with README.md** - Understand current project phase and status
2. **Review architecture.md** - Understand tech stack and design constraints
3. **Check feature files** - For specific implementation details
4. **Reference data-schema.md** - For data structure requirements

## Key Development Principles

### Architecture Standards
- **Simplicity First**: Keep solutions as simple as possible
- **No Additional Features**: Only implement approved features
- **Cloud Service Selection**: Consider cost, security, scalability, and complexity
- **Modern Approaches**: Use online research to validate implementation patterns
- **Compatibility Focus**: Document known issues between services/versions

### Code Generation Rules
- **No code generation until architecture.md is reviewed**
- **Follow existing patterns in the codebase**
- **Validate compatibility across all services**
- **Document any deviations from standards**

### Current Implementation Status
- **Phase 3 Complete**: Historical sensor data ingestion implemented
- **Tech Stack**: Python 3.11, urllib (built-in), Azure Functions, ArcGIS Online
- **Architecture**: REST API approach for reliable deployment and performance

## File Navigation

For specific tasks, reference the appropriate documentation:
- **Understanding the project** → README.md
- **Technical architecture** → architecture.md  
- **Sensor data processing** → app-sensor-ingestion.md
- **ArcGIS connectivity** → app-arcgis-integration.md
- **Data queries** → app-data-queries.md
- **System monitoring** → app-health-monitoring.md
- **Infrastructure deployment** → app-infrastructure-deployment.md
- **Data structures** → data-schema.md

## Documentation Maintenance Requirements

### IMPORTANT: Documentation Synchronization

**Claude Code MUST maintain and update documentation throughout development:**

1. **When Adding New Features**:
   - Create corresponding `app-[feature-name].md` file with complete implementation details
   - Update README.md to reference the new feature
   - Add feature to the Available Documentation Files list below

2. **When Modifying Existing Features**:
   - Update the corresponding feature .md file immediately
   - Ensure compatibility information in architecture.md stays current
   - Update data-schema.md if data structures change

3. **When Changing Architecture**:
   - Update architecture.md with new tech stack decisions
   - Document compatibility issues and resolutions
   - Update field mappings in data-schema.md if affected

4. **Documentation Standards**:
   - All .md files must contain complete, production-ready documentation
   - Include code examples, error handling patterns, and troubleshooting guidance
   - Document known compatibility issues and bugs that inform decisions
   - Provide links to online resources that validate implementation approaches

5. **Version Control**:
   - Update file modification dates in documentation
   - Maintain compatibility matrices in architecture.md
   - Track implementation status in README.md

## Project Context

This is an Azure Function App that receives sensor data via REST API and stores it in ArcGIS Online hosted feature services. The project demonstrates Infrastructure as Code deployment with GitHub Actions and focuses on historical data ingestion for sensor monitoring and alerting systems.