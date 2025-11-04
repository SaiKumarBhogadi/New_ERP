pipeline {
    agent any

    environment {
        BACKEND_DIR = "${WORKSPACE}/erp_project"
        VENV_DIR = "${BACKEND_DIR}/venv"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "📥 Cloning repository..."
                checkout scm
            }
        }

        stage('Setup Virtual Environment & Install Dependencies') {
            steps {
                sh '''
                echo "⚙️ Setting up virtual environment..."
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
                echo "🏗️ Applying database migrations and collecting static files..."
                . "${VENV_DIR}/bin/activate"
                cd "${BACKEND_DIR}"
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput || true
                '''
            }
        }

        stage('Restart Gunicorn & Nginx Services') {
            steps {
                sh '''
                echo "🔁 Restarting Gunicorn and Nginx services..."
                sudo systemctl daemon-reexec
                sudo systemctl daemon-reload
                sudo systemctl restart gunicorn
                sudo systemctl restart nginx
                sudo systemctl enable gunicorn
                sudo systemctl enable nginx
                echo "✅ Gunicorn & Nginx restarted successfully!"
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                echo "🧪 Running smoke test..."
                sleep 5
                if curl -sSf http://127.0.0.1:8000/admin >/dev/null; then
                    echo "✅ Smoke test passed! Backend is reachable."
                else
                    echo "❌ Smoke test failed: 127.0.0.1:8000 not reachable"
                    exit 1
                fi
                '''
            }
        }
    }

    post {
        success {
            echo "🎉 Backend CI/CD pipeline completed successfully!"
        }
        failure {
            echo "🚨 Backend pipeline failed — check Jenkins logs."
        }
    }
}
