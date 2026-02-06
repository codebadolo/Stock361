# télécharger_static.py
import os
import requests

# Créez le dossier static
static_dir = os.path.join(os.path.dirname(__file__), 'static')
vendor_dir = os.path.join(static_dir, 'vendor')

# Structure des dossiers
dirs = [
    os.path.join(vendor_dir, 'bootstrap', 'css'),
    os.path.join(vendor_dir, 'bootstrap', 'js'),
    os.path.join(vendor_dir, 'bootstrap-icons', 'font'),
    os.path.join(vendor_dir, 'datatables', 'css'),
    os.path.join(vendor_dir, 'datatables', 'js'),
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Fichiers à télécharger
files = {
    # Bootstrap 5.3.2
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css': 
        'vendor/bootstrap/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js': 
        'vendor/bootstrap/js/bootstrap.bundle.min.js',
    
    # Bootstrap Icons
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css': 
        'vendor/bootstrap-icons/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff2': 
        'vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff2',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff': 
        'vendor/bootstrap-icons/font/fonts/bootstrap-icons.woff',
    
    # DataTables
    'https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css': 
        'vendor/datatables/css/jquery.dataTables.min.css',
    'https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css': 
        'vendor/datatables/css/dataTables.bootstrap5.min.css',
    'https://code.jquery.com/jquery-3.7.0.min.js': 
        'vendor/jquery/jquery-3.7.0.min.js',
    'https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js': 
        'vendor/datatables/js/jquery.dataTables.min.js',
    'https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js': 
        'vendor/datatables/js/dataTables.bootstrap5.min.js',
    
    # DataTables Buttons
    'https://cdn.datatables.net/buttons/2.4.1/css/buttons.bootstrap5.min.css': 
        'vendor/datatables/css/buttons.bootstrap5.min.css',
    'https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js': 
        'vendor/datatables/js/dataTables.buttons.min.js',
    'https://cdn.datatables.net/buttons/2.4.1/js/buttons.bootstrap5.min.js': 
        'vendor/datatables/js/buttons.bootstrap5.min.js',
    'https://cdn.datatables.net/buttons/2.4.1/js/buttons.colVis.min.js': 
        'vendor/datatables/js/buttons.colVis.min.js',
    'https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js': 
        'vendor/datatables/js/buttons.html5.min.js',
    'https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js': 
        'vendor/datatables/js/buttons.print.min.js',
    
    # Autres plugins DataTables
    'https://cdn.datatables.net/select/1.7.0/css/select.bootstrap5.min.css': 
        'vendor/datatables/css/select.bootstrap5.min.css',
    'https://cdn.datatables.net/select/1.7.0/js/dataTables.select.min.js': 
        'vendor/datatables/js/dataTables.select.min.js',
    'https://cdn.datatables.net/responsive/2.5.0/css/responsive.bootstrap5.min.css': 
        'vendor/datatables/css/responsive.bootstrap5.min.css',
    'https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js': 
        'vendor/datatables/js/dataTables.responsive.min.js',
    'https://cdn.datatables.net/responsive/2.5.0/js/responsive.bootstrap5.min.js': 
        'vendor/datatables/js/responsive.bootstrap5.min.js',
    
    # ZIP, PDFMake pour l'export
    'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js': 
        'vendor/jszip/jszip.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js': 
        'vendor/pdfmake/pdfmake.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js': 
        'vendor/pdfmake/vfs_fonts.js',
}

# Télécharger les fichiers
for url, local_path in files.items():
    full_path = os.path.join(static_dir, local_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    print(f"Téléchargement: {url}")
    response = requests.get(url)
    
    with open(full_path, 'wb') as f:
        f.write(response.content)
    
    print(f"  → {local_path}")

print("Tous les fichiers ont été téléchargés !")