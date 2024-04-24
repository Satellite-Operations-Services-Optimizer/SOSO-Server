const FtpSrv = require("ftp-srv");
const bunyan = require("bunyan");
const port = 8085;

const quietLog = bunyan.createLogger({
  name: "quiet-logger",
  level: 50,
});

const ftpServer = new FtpSrv({
  log: quietLog,
  url: "ftp://127.0.0.1:" + port,
  anonymous: true,
  greeting: "Connection succesful",
});

ftpServer.on("login", ({ connection, username, password }, resolve, reject) => {
  return resolve({
    root: "./FileSystem",
  });
});

ftpServer.listen().then(() => {
  console.log("Ftp server has started");
});

ftpServer.on("client-error", ({ connection, context, error }) => {
  console.log(error.GeneralError);
});

ftpServer.on("STOR", (error, fileName) => {
  console.log("File with name (" + fileName + ") has been uploaded.");
});

ftpServer.on("RETR", (error, fileName) => {
  console.log("File with name (" + fileName + ") has been downloaded.");
});
