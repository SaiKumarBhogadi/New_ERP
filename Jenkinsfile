pipeline {
    agent any

    environment {
        PROJECT_DIR = "/var/lib/jenkins/erp_backend_qa"
        VENV_DIR = "${PROJECT_DIR}/venv"
        REPO_URL = "https://github.com/vasavamshi-vv/New_ERP_Backend.git"
        BRANCH = "qa"
    }

    stages {
        stage('📥 Pull Latest Code') {
            steps {
                echo "Fetching latest code from QA branch..."
                sh '''
                if [ ! -d "$PROJECT_DIR" ]; then
                    mkdir -p $PROJECT_DIR
                fi
                cd $PROJECT_DIR
                if [ ! -d ".git" ]; then
                    git clone -b $BRANCH $REPO_URL .
                else
                    git fetch origin $BRANCH
                    git reset --hard origin/$BRANCH
                fi
                '''
            }
        }

        stage('📦 Install Dependencies') {
            steps {
                echo "Installing Python dependencies..."
                sh '''
                cd $PROJECT_DIR/erp_project
                if [ ! -d "$VENV_DIR" ]; then
                    python3 -m venv $VENV_DIR
                fi
                source $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                deactivate
                '''
            }
        }

        stage('🧹 Apply Migrations & Collect Static Files') {
            steps {
                echo "Running migrations and collecting static files..."
                sh '''
                cd $PROJECT_DIR/erp_project
                source $VENV_DIR/bin/activate
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput
                deactivate
                '''
            }
        }

        stage('🚀 Restart Gunicorn & Nginx') {
            steps {
                echo "Restarting Gunicorn and Nginx..."
                sh '''
                sudo systemctl daemon-reload || true
                sudo systemctl restart gunicorn || true
                sudo systemctl restart nginx || true
                '''
            }
        }

        stage('🧪 Smoke Test') {
            steps {
                echo "Testing Django admin page..."
                sh '''
                curl -I http://localhost/admin/ || echo "Admin not reachable yet!"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ QA Backend Deployed Successfully on ${env.NODE_NAME}"
        }
        failure {
            echo "❌ Deployment Failed! Please check Jenkins logs."
        }
    }
}
