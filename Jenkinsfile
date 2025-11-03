pipeline {
    agent any

    environment {
        # Jenkins WORKSPACE is the checkout directory for this job
        BACKEND_DIR = "${WORKSPACE}/erp_project"
        VENV_DIR = "${BACKEND_DIR}/venv"
    }

    stages {

        stage('Checkout') {
            steps {
                // Jenkins will still checkout the repository before running stages;
                // keep this to clearly show which repo is used by this job
                git branch: 'main', credentialsId: 'github-token', url: 'https://github.com/vasavamshi-vv/New_ERP_Backend.git'
            }
        }

        stage('Setup Virtual Environment & Install Requirements') {
            steps {
                sh '''
                set -euo pipefail
                echo "WORKSPACE=${WORKSPACE}"
                echo "Using BACKEND_DIR=${BACKEND_DIR}"

                # ensure backend dir exists
                if [ ! -d "${BACKEND_DIR}" ]; then
                  echo "Error: ${BACKEND_DIR} not found"
                  exit 1
                fi

                cd "${BACKEND_DIR}"

                # create venv if not exists
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
                set -euo pipefail
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
                # restart system services (requires sudo setup in /etc/sudoers for jenkins/ubuntu)
                sudo systemctl restart gunicorn || true
                sudo systemctl restart nginx || true
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                # check local backend endpoint (gunicorn should bind to 127.0.0.1:8000 or socket as configured)
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
