# Jenkins CI/CD Pipeline to host Flask Application 



### Github Actions 

- This code check if there are any conflicts to merge with master branch
- If any problem persists it would break the pipeline and there would be no build triggered
- If the build fails there would be no build made and hence it won't be deployed and deployed build be a previous successfull build


```
name: CI/CD Pipeline

on:
  push:
    branches:
      - master

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Acknowledging Stage Env
        run: |
          echo "----This change is meant for Stage.-----"
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x' 
      
      - name: Install dependencies
        run: |
          echo "------Installing Dependencies------"
          pip install --upgrade pip
          pip install flask pytest
          echo "------Completed Installing Dependencies-------"
      - name: Run tests
        run: |
          echo "-------Running Test Script-------"
          pytest --disable-warnings -q
      - name: Build Application
        run: |
          echo "-------Building application-------"
  stage-deploy:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - name: Checking Stage Release & Configuring libraries
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST_STG }}
          username: ${{ secrets.EC2_USERNAME_STG }}
          key: ${{ secrets.EC2_SSH_KEY_STG }}
          port: 22
          script: |
            echo "-------This is New Release preparing for stage rollout.-------- "
            sudo apt-get update
            sudo apt update
            sudo apt install python -y
            curl -sS https://bootstrap.pypa.io/get-pip.py | python3
            sudo apt install python3-pip -y
            sudo apt install nginx -y
            pip install flask pytest
      - name: Deploying App in STAGE
        uses: appleboy/scp-action@v0.1.4
        with:
          host: ${{ secrets.EC2_HOST_STG }}
          username: ${{ secrets.EC2_USERNAME_STG }}
          key: ${{ secrets.EC2_SSH_KEY_STG }}
          port: 22
          source: ./
          target: ./
          script: |
            echo "Deploying App in STAGE"
            sudo rm -rf  /etc/nginx/sites-available/default
            sudo cp /home/ubuntu/default /etc/nginx/sites-available/
            sudo systemctl restart nginx
            cd /home/ubuntu/Jenkins0_0
            python3 app.py
```

### Jenkinsfile file to do stage work

- Once build in get sucessfull by scm poll in jenkins configuration the stage work gets triggered.
- Changes made by developer would be shared to hosted directory and hence it would apply changes in deployment.

```
pipeline {
    agent any

    environment {
        DEPLOY_DIR = "/home/ubuntu/Jenkins0_0"
        GIT_REPO = "https://github.com/Gani-23/Jenkins0_0"
        HOSTEDSERVER = "13.125.200.61"
        CREDENTIALS_ID = "Gani" 
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'master', url: "${env.GIT_REPO}"
            }
        }
        stage('Install Dependencies') {
            steps {
                script {
                    sh '''
                    su
                    '''
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        stage('Test') {
            steps {
                script {
                    sh '''
                    . venv/bin/activate
                    pytest
                    '''
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    withCredentials([sshUserPrivateKey(credentialsId: "${env.CREDENTIALS_ID}", keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                        sh """
                        scp -o StrictHostKeyChecking=no -i ${SSH_KEY} -r * ${SSH_USER}@${env.HOSTEDSERVER}:${env.DEPLOY_DIR}
                        ssh -o StrictHostKeyChecking=no -i ${SSH_KEY} ${SSH_USER}@${env.HOSTEDSERVER} <<EOF
cd ${DEPLOY_DIR}
. venv/bin/activate
sudo apt update -y
sudo apt install python3-pip -y
sudo apt install python3-flask -y
pip install -r requirements.txt 
nohup python3 app.py > flaskapp.log 2>&1 &
EOF
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "Build completed with status: ${currentBuild.result}"
            }
        }
    }
}

```
