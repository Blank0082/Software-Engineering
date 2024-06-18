const express = require('express');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const cors = require('cors');
const {exec} = require('child_process');
const fileUpload = require('express-fileupload');
const fs = require('fs');
const path = require('path');

const platform=process.platform;

const secretOrPublicKey = 'secret123';

const authMiddleware = (req, res, next) => {
    const token = req.cookies.token;
    if (!token) {
        return res.status(401).json({ status: 'error', error: 'Unauthorized' });
    }
    try {
        const decoded = jwt.verify(token, secretOrPublicKey);
        req.username = decoded.username;
        next();
    } catch (err) {
        return res.status(401).json({ status: 'error', error: 'Invalid token' });
    }
};

const app = express();
app.use(cors({
    origin: 'http://localhost:3000', // 根據前端應用的地址設置
    credentials: true
}));
app.use(express.json());
app.use(fileUpload());
app.use(cookieParser());


const mongoUri = 'mongodb://localhost:27017/SW';

mongoose.connect(mongoUri).then(() => {
    console.log('Connected to MongoDB');
}).catch(err => {
    console.error('Error connecting to MongoDB', err);
});

const userSchema = new mongoose.Schema({
    username: {type: String, required: true, unique: true},
    password: {type: String, required: true},
});
const User = mongoose.model('User', userSchema);

const fileSchema = new mongoose.Schema({
    originalFilename: {type: String, required: true},
    filename: {type: String, required: true},
    filepath: {type: String, required: true},
    result: {type: String, required: true},
    user: {type: String, required: true},
    uploadDate: {type: Date, default: Date.now}
});

const File = mongoose.model('File', fileSchema);


app.post('/register', async (req, res) => {
    const {username, password} = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    try {
        const user = await User.create({username, password: hashedPassword});
        console.log('User created:', user);
        res.json({status: 'success'});
    } catch (err) {
        if (err.code === 11000) {
            res.status(409).json({status: 'error', error: 'Duplicate username'});
        } else {
            console.error('Error creating user:', err); 
            res.status(500).json({status: 'error', error: 'Server error'});
        }
    }
});


app.post('/login', async (req, res) => {
    const {username, password} = req.body;
    try {
        const user = await User.findOne({username});
        if (!user) {
            return res.status(401).json({status: 'error', error: 'Invalid username/password'});
        }
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(401).json({status: 'error', error: 'Invalid username/password'});
        }
        const token = jwt.sign(
            {username: user.username},
            secretOrPublicKey,
            {expiresIn: '2h', algorithm: 'HS256'}
        );
        res.cookie('token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV !== 'development',
            maxAge: 7200000,
            sameSite: 'None',
        });

        return res.json({status: 'success'});
    } catch (err) {
        res.status(500).json({status: 'error', error: 'Server error'});
    }
});


app.post('/upload',authMiddleware, async (req, res) => {
    const username  = req.username;
    if (!req.files || Object.keys(req.files).length === 0) {
        return res.status(400).json({status: 'error', error: 'No files were uploaded.'});
    }

    const files = Array.isArray(req.files.files) ? req.files.files : [req.files.files];


    if(files.map(file => file.size).reduce((a, b) => a + b, 0) > 30 * 1024 * 1024) {
        return res.status(413).json({status: 'error', error: 'Total file size exceeds 30MB.'});
    }

    const uploadDir = './uploads';
    if (!fs.existsSync(uploadDir)) {
        fs.mkdirSync(uploadDir);
    }

    const uploadAndProcessFile = async (file) => {
        const fileType = file.mimetype;
        if (fileType !== 'image/png' && fileType !== 'image/jpeg') {
            throw new Error('Only PNG and JPG files are allowed.');
        }
        const originalFilename = file.name;
        const uniqueFilename = `${Date.now()}-${originalFilename.replace(/\s+/g, '-')}`;
        const uploadPath = path.join(uploadDir, uniqueFilename);

        await file.mv(uploadPath);

        let command;
        if (platform === 'win32') {
            command = `run.bat ../${uploadPath}`;
        } else {
            command = `./run.sh ../${uploadPath}`;
        }

        const execResult = await new Promise((resolve, reject) => {
            exec(command, {timeout: 3600000}, async (error, stdout, stderr) => {
                if (error) {
                    console.error(`exec error: ${error}`);
                    reject(new Error('Error executing Python script'));
                }else if (!stdout) {
                    console.error('No output from Python script');
                    reject(new Error('No output from Python script'));

                }else {
                    try {
                        const parsedOutput = JSON.parse(stdout.trim());
                        if (parsedOutput.status === 'error') {
                            resolve({
                                ...parsedOutput,
                                filename: originalFilename
                            });
                        } else {
                            resolve({
                                ...parsedOutput,
                                filename: uniqueFilename
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing JSON output from Python script:', e);
                        reject(new Error('Error parsing JSON output from Python script'));
                    }
                }
            });
        });
        if (execResult.status === 'error') {
            fs.unlink(uploadPath, (err) => {
                if (err) {
                    console.error(`Failed to delete file: ${uploadPath}`, err);
                } else {
                    console.log(`Successfully deleted file: ${uploadPath}`);
                }
            });
        }else{
            const newFile = new File({
                originalFilename: originalFilename,
                filename: uniqueFilename,
                filepath: uploadPath,
                result: execResult.data,
                user: username
            });
            await newFile.save();
        }
        return execResult;
    };

    try {
        const results = await Promise.all(files.map(file => uploadAndProcessFile(file)));
        console.log(results);
        res.json({status: 'success', results});
    } catch (err) {
        console.error('Error processing files:', err);
        res.status(500).json({status: 'error', error: err.message});
    }
});


app.get('/history', authMiddleware,async (req, res) => {
    const username = req.username;
    try {
        const files = await File.find({user: username}).sort({uploadDate: -1});
        res.json({status: 'success', files: files});
    } catch (err) {
        res.status(500).json({status: 'error', error: 'Database query error'});
    }
});

app.get('/results/:filename', authMiddleware, async (req, res) => {
    const filename = req.params.filename;
    const username = req.username;

    try {
        const file = await File.findOne({ filename: filename, user: username });
        if (!file) {
            return res.status(403).json({ status: 'error', error: 'Forbidden' });
        }

        res.json({ status: 'success', data: file.result , originalFilename: file.originalFilename});
    } catch (err) {
        res.status(500).json({ status: 'error', error: 'Database query error' });
    }
});
app.post('/saveResults', authMiddleware, async (req, res) => {
    const { results } = req.body;
    const username = req.username;

    try {
        for (let result of results) {
            if (result.status === 'success') {
                await File.updateOne(
                    { filename: result.filename, user: username },
                    { $set: { result: result.data } }
                );
            }
        }
        res.json({status: 'success'});
    } catch (err) {
        res.status(500).json({ status: 'error', error: 'Database update error' });
    }
});

app.put('/saveHistoryResult/:id', authMiddleware, async (req, res) => {
    const fileId = req.params.id;
    const data = req.body;
    const username = req.username;

    try {
        const file = await File.findOne({ _id: fileId, user: username });
        if (!file) {
            return res.status(403).json({ status: 'error', error: 'Forbidden' });
        }
        await File.updateOne(
            { _id: fileId, user: username },
            { $set: { result: data.result } }
        );
        res.json({ status: 'success' });
    }catch (err) {
        res.status(500).json({ status: 'error', error: 'Database update error' })
    };
});

app.get('/uploads/:filename',authMiddleware, async (req, res) => {
    
    const filename = req.params.filename;
    const username = req.username;
    try {
        const file = await File.findOne({filename: filename, user: username});
        if (!file) {
            return res.status(403).json({status: 'error', error: 'Forbidden'});
        }

        const filePath = path.join(__dirname, file.filepath);
        res.sendFile(filePath);
    } catch (err) {
        res.status(500).json({status: 'error', error: 'Database query error'});
    }
});


app.post('/logout', (req, res) => {
    res.clearCookie('token', {sameSite: 'None', secure: process.env.NODE_ENV !== 'development'});
    res.send('Logged out');
});

app.get('/checkAuth', (req, res) => {
    const token = req.cookies.token;
    if (!token) {
        return res.status(401).json({status: 'error', error: 'No token found'});
    }
    try {
        const decoded = jwt.verify(token, secretOrPublicKey);
        res.json({status: 'success', user: decoded.username});
    } catch (err) {
        res.status(401).json({status: 'error', error: 'Invalid token'});
    }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
