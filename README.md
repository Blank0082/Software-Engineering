# Software Engineering Project

This project includes a Node.js backend service and a React frontend application, along with MongoDB as the database.

## Prerequisites

### Node.js and npm

1. **Install Node.js and npm:**

   - **Download and install Node.js:** Go to the [Node.js website](https://nodejs.org/) and download the latest LTS (Long Term Support) version.
   - **Verify the installation:** Open a terminal and run the following commands to check if Node.js and npm are installed correctly.

     ```sh
     node -v
     npm -v
     ```

     You should see the version numbers of Node.js and npm.

### MongoDB

#### Windows

1. **Download MongoDB:**

   - Go to the [MongoDB Download Center](https://www.mongodb.com/try/download/community) and download the MongoDB Community Server for Windows.

   - Run the installer and follow the setup instructions.

   - Add MongoDB to the system PATH. During installation, ensure that the "Install MongoDB as a Service" option is selected.

2. **Verify the installation:**

   Open a terminal and run:

   ```sh
   mongod --version

   You should see the version number of MongoDB.
   ```

#### macOS

1. **Download MongoDB:**
   If you have Homebrew installed, you can use the following command to install MongoDB:

   ```
   brew tap mongodb/brew
   brew install mongodb-community@6.0
   ```

   If you don't have Homebrew, you can download MongoDB from the [MongoDB Download Center](https://www.mongodb.com/try/download/community) and follow the installation instructions.

2. **Start MongoDB:**

   - Start MongoDB as a background service:

   ```
   brew services start mongodb/brew/mongodb-community
   ```

3. **Verify the installation:**

   Open a terminal and run:

   ```
   mongod --version
   ```

   You should see the version number of MongoDB.

# Backend (Node.js)

1. **Navigate to the backend directory:**

   ```
   cd backend
   ```

2. **Install dependencies:**

   ```
   npm install
   ```

3. **Start the backend server:**

   ```
   npm start
   ```

   The server will start on `http://localhost:5000`.

# Frontend (React)

1. **Navigate to the frontend directory:**

   ```
   cd simpleWebsite
   ```

2. **Install dependencies:**

   ```
   npm install
   ```

3. **Start the frontend development server:**

   ```
   npm start
   ```

   The application will be available at `http://localhost:3000`.

4. **Access the application:**

   Open your web browser and visit `http://localhost:3000` to see the application in action.

5. **Stopping the servers:**

   To stop the backend server, press `Ctrl + C` in the terminal where it's running.
   To stop the frontend development server, press `Ctrl + C` in the terminal where it's running.

6. **Troubleshooting:**

   If you encounter any issues during the setup or installation process, please refer to the documentation for the specific technology (Node.js, MongoDB, React) for troubleshooting steps.
