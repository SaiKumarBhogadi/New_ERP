pipeline {
    agent any

    environment {
        BACKEND_DIR = "${WORKSPACE}/erp_project"
        VENV_DIR = "${BACKEND_DIR}/venv"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', credentialsId: 'github-token', url: 'https://github.com/vasavamshi-vv/New_ERP_Backend.git'
            }
        }

        stage('Setup Virtual Environment & Install Requirements') {
            steps {
                sh '''
                set -e
                echo "WORKSPACE=${WORKSPACE}"
                echo "Using BACKEND_DIR=${BACKEND_DIR}"

                if [ ! -d "${BACKEND_DIR}" ]; then
                  echo "Error: ${BACKEND_DIR} not found"
                  exit 1
                fi

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
                set -e
                . "${VENV_DIR}/bin/activate"
                cd "${BACKEND_DIR}"
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput
                '''
            }
        }

        stage('Restart Backend Services') {
            steps {
                sh '''
                sudo systemctl restart gunicorn || true
                sudo systemctl restart nginx || true
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                if curl -sSf http://127.0.0.1:8000/ >/dev/null 2>&1; then
                  echo "Smoke test OK (127.0.0.1:8000 reachable)"
                else
                  echo "Smoke test failed: 127.0.0.1:8000 not reachable"
                  exit 1
                fi
                '''
            }
        }
    }

    post {
        success { echo "✅ Backend pipeline completed successfully" }
        failure { echo "❌ Backend pipeline failed — check logs." }
    }
}
