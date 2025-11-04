pipeline {
    agent any

    environment {
        BACKEND_DIR = "${WORKSPACE}/erp_project"
        VENV_DIR = "${BACKEND_DIR}/venv"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Cloning repository..."
                checkout scm
            }
        }

        stage('Setup Virtual Environment & Install Dependencies') {
            steps {
                sh '''
                echo "Setting up virtual environment..."
                cd "${BACKEND_DIR}"
                if [ ! -d "${VENV_DIR}" ]; then
                    python3 -m venv "${VENV_DIR}"
                fi
                . "${VENV_DIR}/bin/activate"
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Migrate & Collectstatic') {
            steps {
                sh '''
                echo "Applying database migrations and collecting static files..."
                . "${VENV_DIR}/bin/activate"
                cd "${BACKEND_DIR}"
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput || true
                '''
            }
        }

        stage('Restart Gunicorn Service') {
            steps {
                sh '''
                echo "Restarting Gunicorn service..."
                sudo systemctl restart gunicorn
                sudo systemctl status gunicorn --no-pager
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                echo "Running smoke test..."
                sleep 5
                curl -I http://127.0.0.1:8000/admin || { echo "Smoke test failed: backend not reachable"; exit 1; }
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Backend pipeline executed successfully!"
        }
        failure {
            echo "❌ Backend pipeline failed — check logs."
        }
    }
}
