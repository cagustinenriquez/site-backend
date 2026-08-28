# Getting Started

## Prerequisites

- Node.js 18+ 
- npm or yarn

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/agustinenriquez/site-backend.git
   cd site-backend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Setup**
   
   Create a `.env` file in the root directory with the required variables:
   ```env
   NODE_ENV=development
   PORT=3000
   # Add other required environment variables here
   ```

## Development

### Start the development server

```bash
npm run dev
```

The server will start at `http://localhost:3000`.

### Run tests

```bash
npm test
```

Watch mode:
```bash
npm run test:watch
```

### Build for production

```bash
npm run build
```

## Project Structure

```
src/
├── index.js              # Application entry point
├── routes/               # API route handlers
├── controllers/          # Business logic
├── models/               # Data models
├── middleware/           # Express middleware
├── utils/                # Utility functions
└── config/               # Configuration files
```

## Troubleshooting

### Port already in use
If port 3000 is already in use, specify a different port:
```bash
PORT=3001 npm run dev
```

### Dependencies installation issues
Try clearing npm cache:
```bash
npm cache clean --force
npm install
```

## Next Steps

- Read the [API documentation](./API.md) to understand the available endpoints
- Check out the [CONTRIBUTING.md](./CONTRIBUTING.md) guide before submitting changes
