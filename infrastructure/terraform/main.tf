{
  "name": "document-management-ai-chatbot",
  "version": "1.0.0",
  "description": "Document Management and AI Chatbot System - Backend API for intelligent document search and retrieval capabilities",
  "main": "index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext .js,.jsx",
    "format": "prettier --write \"**/*.{js,jsx,json,md}\"",
    "test": "jest",
    "postinstall": "echo 'Python backend dependencies must be installed separately with pip or poetry'"
  },
  "dependencies": {
    "axios": "^1.5.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "express": "^4.18.2",
    "jsonwebtoken": "^9.0.2",
    "openai": "^4.0.0",
    "swagger-ui-express": "^5.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.1.2",
    "@testing-library/react": "^14.0.0",
    "eslint": "^8.48.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-import": "^2.28.1",
    "eslint-plugin-jest": "^27.2.3",
    "eslint-plugin-prettier": "^5.0.0",
    "jest": "^29.6.4",
    "prettier": "^3.0.3",
    "supertest": "^6.3.3",
    "vite": "^4.4.9"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/your-org/document-management-ai-chatbot.git"
  },
  "keywords": [
    "document-management",
    "ai",
    "chatbot",
    "vector-search",
    "faiss",
    "llm",
    "fastapi"
  ],
  "author": "Your Organization",
  "license": "MIT",
  "bugs": {
    "url": "https://github.com/your-org/document-management-ai-chatbot/issues"
  },
  "homepage": "https://github.com/your-org/document-management-ai-chatbot#readme"
}