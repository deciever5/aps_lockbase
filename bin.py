<<div class="container-fluid">
         <div class="row">
            <div class="col-md-6">
                <form method="post" enctype="multipart/form-data" class="mx-auto mt-5 py-4">
                  <div class="form-group">
                      <label for="pdf-file">Upload CSV file:</label>
                    <input type="file" name="file" accept="application/pdf" id="pdf_file" class="form-control-file">
                  </div>
                  <button type="submit" class="btn btn-primary">Wyślij PDF</button>
                </form>
            </div>

            <div class="col-md-6">
                <form action="/upload-csv" method="post" enctype="multipart/form-data">
                      <div class="form-group">
                        <label for="csv-file">Upload CSV file:</label>
                        <input type="file" class="form-control-file" id="csv-file" name="csv-file" accept=".csv">
                      </div>
                      <button type="submit" class="btn btn-primary">Upload</button>
                </form>
            </div>
        </div>
        </div>

nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
          <div class="container">
            <a class="navbar-brand" href="#">Konwerter plików LOCKBASE do APS</a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
              <ul class="navbar-nav">
                <li class="nav-item active">
                  <a class="nav-link" href="#">Konwerter</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#">Archiwum zleceń</a>
                </li>
                <li class="nav-item">
                  <a class="nav-link" href="#">Kontakt</a>
                </li>
              </ul>
            </div>
          </div>
        </nav>