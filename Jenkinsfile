pipeline {
    agent any

    environment {
        PROJECT_DIR = '/home/ubuntu/ERP-Backend-QA/erp_project'
        VENV_DIR = "${PROJECT_DIR}/venv"
        SERVICE_NAME = 'gunicorn_qa'
    }

    stages {

        stage('📥 Pull Latest Code') {
            steps {
                echo "Fetching latest code from QA branch..."
                dir("${PROJECT_DIR}") {
                    sh '''
                        git fetch origin qa
                        git checkout qa
                        git reset --hard origin/qa
                    '''
                }
            }
        }

        stage('📦 Install Dependencies') {
            steps {
                echo "Installing Python dependencies..."
                sh '''
                    cd ${PROJECT_DIR}
                    if [ ! -d "${VENV_DIR}" ]; then
                        python3 -m venv ${VENV_DIR}
                    fi
                    source ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('🧹 Apply Migrations & Collect Static Files') {
            steps {
                echo "Applying database migrations..."
                sh '''
                    source ${VENV_DIR}/bin/activate
                    cd ${PROJECT_DIR}
                    python3 manage.py migrate
                    python3 manage.py collectstatic --noinput || true
                '''
            }
        }

        stage('🚀 Restart Gunicorn & Nginx') {
            steps {
                echo "Restarting Gunicorn & Nginx services..."
                sh '''
                    sudo systemctl daemon-reload
                    sudo systemctl restart ${SERVICE_NAME}
                    sudo systemctl restart nginx
                    sudo systemctl enable ${SERVICE_NAME}
                '''
            }
        }

        stage('🧪 Smoke Test') {
            steps {
                echo "Running smoke test on QA server..."
                script {
                    def result = sh(
                        script: "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/admin",
                        returnStdout: true
                    ).trim()

                    if (result != "302") {
                        error("❌ Smoke test failed! Backend not reachable (HTTP ${result})")
                    } else {
                        echo "✅ Smoke test passed! Admin portal reachable."
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ QA Backend Deployed Successfully on $(hostname)"
        }
        failure {
            echo "❌ Deployment Failed! Please check Jenkins logs."
        }
    }
}
