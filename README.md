# Relationship Chat Reconstruction Webpage

A private, interactive web application to reconstruct, archive, and view relationship chat histories across WhatsApp and Instagram.

## Overview
This repository contains the application codebase, reconstruction tools, and UI components to parse, align, and display relationship chat histories.

> **Privacy Notice**: Raw conversation exports, personal photos, audio notes, and video recordings are excluded from version control (`.gitignore`) to protect personal privacy and ensure sensitive data remains strictly local to your device.

## Project Structure
- `chatgpt_relationship-archive-reconstruction-v3.6/`: Reconstruction pipeline specification, processing tools, references, and test suites.
- `relationship-archive/`: Local workspace for generated archive artifacts and static web bundles.
- `Messages Exports/`: Local directory containing raw chat export data (excluded from Git).

## Security & Privacy Guidelines
- **Local by Default**: The archive is built to be run locally in the browser or delivered as a private local package.
- **No Remote Leakage**: Personal chat records, media files, and sensitive credentials must never be committed to Git or pushed to public servers.
