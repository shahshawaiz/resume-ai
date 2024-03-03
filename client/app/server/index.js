const express = require('express');
const multer = require('multer');
const cors = require('cors');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));



const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'public')
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname)
    }
});

const upload = multer({ storage }).array('file');


app.post('/test', (req, req) => {

})

app.post('/upload', (req, res) => {
    upload(req, res, (err) => {
        if (err) {
            return res.status(500).json(err)
        }
        // get file 
        const files = req.files;
        console.log(files);

        console.log("body json");

        console.log(req.body);

        return res.status(200).send(req.files)
    })
});

app.listen(8000, () => {
    console.log('App is running on port 8000')
});