pipeline {
    agent any

    environment {
        BACKEND_REPO = "https://github.com/vasavamshi-vv/New_ERP_Backend.git"
        FRONTEND_REPO = "https://github.com/vasavamshi-vv/ERP-Frontend.git"

        BACKEND_DIR = "${WORKSPACE}/erp-backend"
        FRONTEND_DIR = "${WORKSPACE}/erp-frontend"

        BACKEND_IMAGE = "erp-backend:dev"
        FRONTEND_IMAGE = "erp-frontend:dev"

        BACKEND_CONTAINER = "erp-backend-dev"
        FRONTEND_CONTAINER = "erp-frontend-dev"
    }

    stages {

        stage('Checkout Both Repos') {
            steps {
                echo "📥 Cloning backend & frontend..."

                dir("${BACKEND_DIR}") {
                    git branch: 'dev', url: "${BACKEND_REPO}"
                }

                dir("${FRONTEND_DIR}") {
                    git branch: 'dev', url: "${FRONTEND_REPO}"
                }
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                script {
                    echo "🐳 Building backend Docker image..."
                    sh """
                        cd ${BACKEND_DIR}
                        docker build -t ${BACKEND_IMAGE} .
                    """
                }
            }
        }

        stage('Deploy Backend Container') {
            steps {
                script {
                    echo "🚀 Deploying backend container..."

                    // --- FIX: Reset Database ---
                    sh """
                        echo "🧹 Cleaning up old database to fix migration conflicts..."
                        rm -f "${WORKSPACE}/erp-backend/erp_project/db.sqlite3"
                        touch "${WORKSPACE}/erp-backend/erp_project/db.sqlite3"
                    """

                    sh """
                        docker rm -f ${BACKEND_CONTAINER} || true

                        docker run -d \
                            --name ${BACKEND_CONTAINER} \
                            --restart unless-stopped \
                            -p 8000:8000 \
                            -e DB_ENGINE=sqlite3 \
                            --env-file "${WORKSPACE}/erp-backend/erp_project/.env.dev" \
                            -v "${WORKSPACE}/erp-backend/erp_project/media:/app/media" \
                            -v "${WORKSPACE}/erp-backend/erp_project/db.sqlite3:/app/db.sqlite3" \
                            ${BACKEND_IMAGE}
                    """
                }
            }
        }

        stage('Build Frontend Docker Image') {
            steps {
                script {
                    echo "🌐 Building frontend Docker image..."
                    sh """
                        cd ${FRONTEND_DIR}
                        docker build -t ${FRONTEND_IMAGE} .
                    """
                }
            }
        }

        stage('Deploy Frontend Container') {
            steps {
                script {
                    echo "🚀 Deploying frontend container..."

                    sh """
                        docker rm -f ${FRONTEND_CONTAINER} || true

                        docker run -d \
                            --name ${FRONTEND_CONTAINER} \
                            --restart unless-stopped \
                            -p 3000:80 \
                            ${FRONTEND_IMAGE}
                    """
                }
            }
        }

        stage('Smoke Tests') {
            steps {
                sh """
                    echo "🧪 Running smoke tests..."
                    
                    sleep 20

                    # Backend test - UPDATED: Pointing to /admin/ because it accepts GET requests
                    # Using -L to follow redirects (Django often redirects /admin -> /admin/login/)
                    curl -sSfL http://localhost:8000/admin/ > /dev/null \
                        && echo "✔ Backend OK" \
                        || (echo "❌ Backend Down (Check logs)" && exit 1)

                    # Frontend test
                    curl -sSf http://localhost:3000 > /dev/null \
                        && echo "✔ Frontend OK" \
                        || (echo "❌ Frontend Down" && exit 1)
                """
            }
        }
    }

    post {
        success {
            echo "🎉 DEV CI/CD pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed. Check logs in Jenkins!"
        }
    }
}
