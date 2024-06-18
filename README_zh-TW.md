# 軟體工程項目

這個項目包括一個 Node.js 後端服務和一個 React 前端應用程式，以及 MongoDB 作為資料庫。

## 前置需求

### Node.js 和 npm

1. **安裝 Node.js 和 npm:**

   - **下載並安裝 Node.js:** 前往 [Node.js 官方網站](https://nodejs.org/)，下載最新的 LTS（長期支援）版本。
   - **驗證安裝:** 打開終端機，運行以下命令以檢查 Node.js 和 npm 是否安裝正確。

     ```
     node -v
     npm -v
     ```

     你應該會看到 Node.js 和 npm 的版本號。

### MongoDB

#### Windows

1. **下載 MongoDB:**

   - 前往 [MongoDB 下載中心](https://www.mongodb.com/try/download/community)，下載適用於 Windows 的 MongoDB 社區版。
   - 執行安裝程式並按照安裝說明進行設置。
   - 將 MongoDB 添加到系統 PATH 中。安裝過程中，確保選擇「Install MongoDB as a Service」選項。

2. **驗證安裝:**

   打開終端機並運行:

   ```
   mongod --version
   ```

   你應該會看到 MongoDB 的版本號。

#### MacOS

1. **使用 Homebrew 安裝 MongoDB:**

   - 如果你還沒有安裝 Homebrew，請按照 [Homebrew 官方文檔](https://brew.sh/) 進行安裝。
   - 打開終端機並運行以下命令以安裝 MongoDB:

   ```
   brew tap mongodb/brew
   brew install mongodb-community@6.0
   ```

2. **啟動 MongoDB 服務:**

   ```
   brew services start mongodb/brew/mongodb-community
   ```

3. **驗證安裝:**

   ```
    mongod --version
   ```

   你應該會看到 MongoDB 的版本號。

# 後端 (Node.js)

1. **導航到後端目錄:**

   ```
   cd backend
   ```

2. **安裝依賴:**

   ```
   npm install
   ```

3. **啟動後端服務:**

   ```
   npm start
   ```

   後端服務現在應該在 `http://localhost:5000` 上運行。

# 前端 (React)

1. **導航到前端目錄:**

    ```
    cd simpleWebsite
    ```

2. **安裝依賴:**

    ```
    npm install
    ```

3. **啟動前端應用程式:**

    ```
    npm start
    ```
    前端應用程式現在應該在 `http://localhost:3000` 上運行。
    你可以在瀏覽器中打開此 URL 以查看應用程式。


    這樣，你就成功地設置了 Node.js 後端服務、React 前端應用程式和 MongoDB 資料庫。