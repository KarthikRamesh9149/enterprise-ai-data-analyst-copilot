# Local Development

Use Python 3.11+ and Node 24+. Generate demo data with `make demo-data`, start Docker with `make up`, migrate with `make migrate`, seed with `make seed`, and open the frontend at `http://localhost:3000`.

Troubleshooting: ensure Docker Desktop is running, ports 3000/5000/5432/6379/8000 are free, and `.env` does not contain production secrets.
