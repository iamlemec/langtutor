// readability server

const http = require('http');
const { extractText } = require('./extract.js');

// create server handler
const app = http.createServer((req, res) => {
    let body = '';
    req.on('data', (chunk) => {
        body += chunk;
    });
    req.on('end', async () => {
        const content = await extractText(body);
        const text = `${content.title}\n\n${content.content}`;
        res.writeHead(200, {'Content-Type': 'text/plain'});
        res.end(text);
    });
});

// get command line port
let [_, __, portString] = process.argv;
const port = Number(portString ?? 3000);

// start server on port
app.listen(port, () => {
    console.log(`Readability server is running on port ${port}`);
});
