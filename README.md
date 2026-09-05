# PhishShield AI

A machine learning system that classifies URLs as legitimate or phishing. This project implements Sprint 1 (data collection & feature extraction), Sprint 2 (model training & selection), and Sprint 3 (Flask API backend with Swagger documentation) of a 4-sprint development plan.

## Project Structure

```
phishshield-ai/
├── app/                   # Flask application (Sprint 3)
│   ├── auth/              # Authentication routes
│   ├── scan/              # URL scanning routes
│   ├── analytics/         # Analytics routes
│   ├── ml/                # ML predictor integration
│   └── models/            # Database models
├── data/
│   ├── raw/              # downloaded datasets, untouched
│   └── processed/        # cleaned/feature-engineered CSVs
├── models/               # saved .pkl model files
├── scripts/              # Utility scripts (seed data, etc.)
├── src/
│   ├── data/
│   │   ├── download_data.py      # download datasets from UCI/Kaggle
│   │   ├── preprocess.py         # clean and merge datasets
│   │   └── generate_sample_data.py  # generate sample data for testing
│   ├── features/
│   │   ├── url_features.py       # reusable feature extraction module
│   │   └── generate_features.py  # batch feature extraction
│   └── models/
│       ├── train.py              # train ML models
│       ├── evaluate.py           # evaluate and compare models
│       └── finalize_model.py     # serialize production model
├── tests/                # Test suite
│   ├── test_auth.py              # Authentication tests
│   ├── test_scan.py              # Scan routes tests
│   ├── test_analytics.py         # Analytics tests
│   └── test_url_features.py     # Feature extraction tests
├── requirements.txt
├── run.py                # Flask application entry point
└── README.md
```

## Features

### URL Feature Extraction
The system extracts the following features from URLs for phishing detection:

- **url_length**: Total length of the URL
- **domain_entropy**: Shannon entropy of the domain (measures randomness)
- **has_https**: Boolean (1 if HTTPS, 0 otherwise)
- **has_ip_address**: Boolean (1 if URL uses IP address instead of domain)
- **dot_count**: Number of dots in the URL
- **subdomain_count**: Number of subdomains
- **special_char_count**: Count of special characters (@, -, _, etc.)
- **redirect_count**: Number of potential redirects in URL structure

### Machine Learning Models
Three candidate models are trained and evaluated:
- **Logistic Regression**: Baseline linear model with feature scaling
- **Random Forest**: Ensemble tree-based model
- **XGBoost**: Gradient boosting framework for structured data

## Installation

### Prerequisites
- Python 3.10 or higher
- Virtual environment (venv)
- Neon Postgres account (for production deployment)

### Setup

1. Clone the repository and navigate to the project directory:
```bash
cd PhishShield-AI
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Set up environment variables:
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env to customize configuration (optional for development)
# The default values work for local development
```

### Database Setup

The application supports both SQLite (for local development) and Neon Postgres (for production).

#### Local Development (SQLite)

By default, the application uses SQLite for local development. No additional setup is required:

```bash
# The .env file defaults to SQLite
DATABASE_URL=sqlite:///phishshield.db
```

#### Production Deployment (Neon Postgres)

For production deployment on Render, we use Neon Postgres for persistent data storage. Neon is a serverless Postgres database with a generous free tier.

**Step 1: Create a Neon Project**

1. Go to [https://neon.tech](https://neon.tech) and sign up for a free account
2. Click "Create a project" 
3. Choose a name for your project (e.g., "phishshield-ai")
4. Select a region (choose one closest to your users)
5. Click "Create Project"

**Step 2: Get Your Connection String**

1. After creating the project, Neon will show you a connection string
2. The connection string will look like:
   ```
   postgresql://username:password@ep-cool-region.aws.neon.tech/database?sslmode=require
   ```
3. Copy this connection string - you'll need it for Render

**Step 3: Configure Render Environment Variables**

1. Go to your Render dashboard
2. Select your PhishShield AI service
3. Navigate to "Environment" section
4. Add a new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste your Neon connection string
5. Make sure the connection string includes `?sslmode=require` (Neon requires SSL)

**Step 4: Deploy**

1. Push your code to GitHub
2. Connect your repository to Render
3. Deploy using the `render.yaml` configuration file
4. The build command will automatically run database migrations
5. Your application will start with persistent Neon Postgres storage

**Important Notes:**
- Never commit real database credentials to the repository
- Use the `.env.example` file as a template with placeholder values only
- Neon's free tier includes 0.5GB storage and sufficient compute for small applications
- The application automatically runs migrations on deployment via the startup script

## Quickstart (Flask API)

Get the Flask API running with Swagger documentation in minutes:

### 1. Setup Database and Seed Demo Data

**For Local Development (SQLite):**
```bash
# Initialize the database and seed with demo data
python scripts/seed_demo_data.py
```

**For Production (Neon Postgres):**
```bash
# Set DATABASE_URL environment variable to your Neon connection string
export DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"

# Run migrations (this also happens automatically on deploy)
python -m flask db upgrade

# Seed demo data (optional - for testing with Neon)
python scripts/seed_demo_data.py
```

This creates demo users with credentials:
- **Regular User**: `demouser` / `DemoPassword123!`
- **Admin User**: `admin` / `AdminPassword123!`

### 2. Start the Flask Server
```bash
python run.py
```

The server will start on `http://127.0.0.1:5000` and display:
```
Swagger docs available at http://127.0.0.1:5000/api/docs
```

### 3. Access Interactive API Documentation
Open your browser and navigate to:
```
http://127.0.0.1:5000/api/docs
```

This provides:
- Interactive Swagger UI for all API endpoints
- Request/response schemas
- "Try it out" functionality for each endpoint
- Authentication examples

### 4. Test the API (Using Swagger UI)

**Step 1: Login**
- Navigate to `POST /api/auth/login`
- Click "Try it out"
- Use demo credentials:
  ```json
  {
    "username": "demouser",
    "password": "DemoPassword123!"
  }
  ```
- Copy the returned `access_token`

**Step 2: Authorize Requests**
- Click the "Authorize" button at the top right
- Enter: `Bearer YOUR_ACCESS_TOKEN`
- Click "Authorize"

**Step 3: Scan a URL**
- Navigate to `POST /api/scan`
- Click "Try it out"
- Enter a URL to analyze:
  ```json
  {
    "url": "https://www.google.com"
  }
  ```
- View the phishing detection results

**Step 4: View Analytics**
- Navigate to `GET /api/analytics/summary`
- Click "Try it out" to view your scan statistics

### 5. Health Check
Verify the API is running:
```bash
curl http://127.0.0.1:5000/api/health
```

## Pipeline Execution

### Option 1: Using Sample Data (Recommended for Testing)

For testing purposes, you can use the included sample data generator:

```bash
# Generate sample data
python src/data/generate_sample_data.py

# Preprocess the data
python src/data/preprocess.py

# Extract features
python src/features/generate_features.py

# Train models
python src/models/train.py

# Evaluate models
python src/models/evaluate.py

# Finalize production model
python src/models/finalize_model.py
```

### Option 2: Using Real Datasets

To use real phishing datasets:

1. **Download Datasets**:
```bash
python src/data/download_data.py
```

   This will attempt to download:
   - UCI Phishing Websites Dataset
   - Kaggle phishing URL dataset (requires `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables)

   If automatic download fails, follow the manual download instructions provided in the script output.

2. **Preprocess Data**:
```bash
python src/data/preprocess.py
```

3. **Extract Features**:
```bash
python src/features/generate_features.py
```

4. **Train Models**:
```bash
python src/models/train.py
```

5. **Evaluate Models**:
```bash
python src/models/evaluate.py
```

6. **Finalize Production Model**:
```bash
python src/models/finalize_model.py
```

## Testing

Run the unit tests for the feature extraction module:

```bash
pytest tests/test_url_features.py -v
```

## Model Performance

The best model is selected based on F1 score, which balances precision and recall for phishing detection. 

### Test Results (Sample Data)
Using the sample dataset (665 URLs after preprocessing, 80/20 train/test split):

**Best Model:** Logistic Regression

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| Logistic Regression | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Random Forest | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| XGBoost | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

**Test Set:** 133 URLs (103 legitimate, 30 phishing)
**Confusion Matrix (Logistic Regression):**
```
[[103   0]
 [  0  30]]
```

*Note: Perfect scores on sample data are expected due to the synthetic nature of the test dataset. Real-world performance will vary with actual phishing datasets.*

After running the evaluation pipeline, check `models/evaluation_report.md` for detailed performance metrics including:
- Accuracy, Precision, Recall, F1 Score for each model
- Confusion matrices
- Detailed classification reports

## Production Model

The final production model is saved as `models/phishshield_model.pkl`. This package includes:
- The trained model
- Preprocessing artifacts (e.g., scaler)
- Feature names for validation
- Metadata about the model type and version

This model is ready to be imported into the Flask backend in Sprint 3.

## Feature Extraction Module

The `src/features/url_features.py` module is designed to be lightweight and reusable. It can be imported directly into the Flask backend for real-time URL classification:

```python
from src.features.url_features import extract_features

# Extract features from a single URL
features = extract_features("https://example.com")
# Returns: {'url_length': 18, 'domain_entropy': 2.5, 'has_https': 1, ...}
```

## Environment Variables

### Application Configuration
- `FLASK_APP`: Flask application entry point (default: `run.py`)
- `FLASK_ENV`: Environment mode (`development` or `production`)
- `SECRET_KEY`: Flask secret key for session management
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `PORT`: Server port (default: 5000)

### Database Configuration
- `DATABASE_URL`: Database connection string
  - **Local development**: `sqlite:///phishshield.db`
  - **Production**: `postgresql://user:password@host/dbname?sslmode=require` (Neon)

### Model Configuration
- `MODEL_PATH`: Path to the trained ML model (default: `models/phishshield_model.pkl`)

### CORS Configuration
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

### Optional Variables
- `KAGGLE_USERNAME`: Your Kaggle username (for dataset download)
- `KAGGLE_KEY`: Your Kaggle API key (for dataset download)

## Development Notes

- **Reproducibility**: All models use consistent random seeds (RANDOM_STATE = 42)
- **Class Imbalance**: Models are configured to handle potential class imbalance using class weights and scale_pos_weight
- **Feature Engineering**: The feature extraction module is dependency-light for fast inference in production
- **Cross-Validation**: Models are evaluated using 5-fold stratified cross-validation

## API Documentation

### Technology Choice: Flasgger

We chose **Flasgger** for API documentation over alternatives like flask-smorest/apispec because:
- **Simplicity**: Decorator-based documentation integrates seamlessly with existing Flask routes
- **Minimal overhead**: No need to rewrite schemas in separate files - documentation lives with the code
- **Swagger UI**: Built-in interactive documentation that's immediately useful
- **Compatibility**: Works well with Flask-JWT-Extended and our existing authentication system
- **Proven**: Battle-tested library with active maintenance and good Flask integration

### Available Endpoints

**Authentication (`/api/auth`)**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout (client-side token discard)
- `GET /api/auth/me` - Get current user info

**Scan (`/api/scan`)**
- `POST /api/scan/` - Submit URL for phishing analysis
- `GET /api/scan/history` - Get paginated scan history
- `GET /api/scan/history/<id>` - Get detailed scan information
- `DELETE /api/scan/history/<id>` - Delete scan record

**Analytics (`/api/analytics`)**
- `GET /api/analytics/summary` - Get summary statistics
- `GET /api/analytics/trends` - Get scan trends over time
- `GET /api/analytics/risk-distribution` - Get risk score distribution

**Admin (`/api/admin`)**
- `GET /api/admin/scans` - View all scan records across all users (admin only)
- `GET /api/admin/users` - List all registered users with scan counts (admin only)
- `DELETE /api/admin/users/{user_id}` - Delete a user account (admin only)
- `PATCH /api/admin/users/{user_id}` - Update user role (admin only)
- `GET /api/admin/activity` - Get system-wide activity statistics (admin only)

**Health**
- `GET /api/health` - API health check with version info
- `GET /health` - Basic health check

### Interactive Documentation

Swagger UI is available at `/api/docs` when the server is running. This provides:
- Complete API documentation
- Request/response schemas
- Interactive "Try it out" functionality
- Authentication examples

### Admin Access

The system includes admin functionality for system administration. Demo admin credentials:
- **Username**: `admin`
- **Password**: `AdminPassword123!`

Admin endpoints allow:
- **View All Scan Records**: See all scans across all users
- **Manage User Accounts**: List, delete, and update user roles
- **Monitor System Activity**: View system-wide statistics and usage patterns

**Data Retention Policy**: When an admin deletes a user account, all associated scan records and ML features are automatically deleted via cascade delete. This ensures data consistency and complies with data retention policies.

## Database Migrations

The application uses Flask-Migrate for database schema management. This ensures that database changes are tracked and applied consistently across deployments.

### Migration Commands

```bash
# Initialize migrations (only needed once)
python -m flask db init

# Generate a new migration
python -m flask db migrate -m "Description of changes"

# Apply migrations to the database
python -m flask db upgrade

# Rollback to previous migration
python -m flask db downgrade

# View current migration version
python -m flask db current
```

### Automatic Migrations

- **Development**: Migrations run automatically when you start the app with `python run.py`
- **Production**: Migrations run automatically during the Render build process via `scripts/startup_migrations.py`
- **Seeding**: The `seed_demo_data.py` script now uses migrations instead of raw SQL

### Data Persistence

With Neon Postgres:
- ✅ Data survives deployments and restarts
- ✅ Automatic backups provided by Neon
- ✅ No data loss when Render spins down your service
- ✅ Easy scaling and connection pooling

With SQLite (local development):
- ✅ No network dependency for development
- ✅ Fast and simple for local testing
- ❌ Data lost on service restart (not suitable for production)

## Deployment

### Render Deployment

The application includes a `render.yaml` configuration file for easy deployment to Render:

1. **Push code to GitHub**
2. **Connect repository to Render**
3. **Configure environment variables:**
   - `DATABASE_URL`: Your Neon Postgres connection string
   - `SECRET_KEY`: Auto-generated by Render
   - `JWT_SECRET_KEY`: Auto-generated by Render
   - `CORS_ORIGINS`: Your frontend domain
4. **Deploy** - Render will automatically:
   - Install dependencies
   - Run database migrations
   - Start the application with Gunicorn

### Manual Verification After Deployment

After deployment, verify the setup:

1. **Check database connectivity:**
   ```bash
   curl https://your-app.onrender.com/api/health
   ```

2. **Test user registration:**
   ```bash
   curl -X POST https://your-app.onrender.com/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"TestPass123!"}'
   ```

3. **Test URL scanning:**
   ```bash
   curl -X POST https://your-app.onrender.com/api/scan/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{"url":"https://example.com"}'
   ```

4. **Trigger a redeploy** to verify data persistence:
   - Make a small code change (e.g., update a comment)
   - Push to GitHub
   - Wait for redeploy to complete
   - Verify your test user and scan data still exist

## Next Steps (Sprint 4)

The next sprint will implement:
- Frontend web interface (React/Vue.js)
- Real-time dashboard with Chart.js visualizations
- User authentication UI
- URL scanning interface
- Analytics dashboard

## License

This project is developed as part of the PhishShield AI system.

## Contributing

This is a development project. For questions or issues, please refer to the project documentation.
