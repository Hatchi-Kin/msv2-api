FROM python:3.12-slim-bookworm

WORKDIR /app

# Install uv
RUN pip install uv

# Copy only uv.lock and pyproject.toml to leverage Docker cache
COPY uv.lock pyproject.toml ./ 

# Install dependencies using uv
RUN uv sync

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
