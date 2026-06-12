#!/usr/bin/env ./local/bin/python

# Standard:
import argparse
from   argparse import RawTextHelpFormatter
from   pathlib import Path
import html

# Third party:
# Own:

# Static program configuration:
DEFAULT_KML_FILE = "routes.kml"
DEFAULT_HTM_FILE = "routes.html"
TILE_COLOR_RGB   = "d187ed"  # Without '#'
TILE_OPACITY     = 0.2


def get_user_args():
	parser = argparse.ArgumentParser(
		description = (
			"Creates a local tiles mesh viewer HTML file using OpenStreetMap\n\n"
			"Author: https://github.com/andre-st/" 
		),
		epilog = (
			"Examples:\n"
			"  ./kml2htm.py\n"
			"  ./kml2htm.py routes.kml\n"
			"  ./kml2htm.py --htm-file=routes.html routes.kml\n"
			"\n"
			"License:\n"
			"   MIT License"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "kml_file",          help=f"input KML file path with tiles, default: {DEFAULT_KML_FILE}", default=DEFAULT_KML_FILE, nargs="?" )
	parser.add_argument( "-o", "--htm-file",  help=f"output HTML file, default: {DEFAULT_HTM_FILE}",               default=DEFAULT_HTM_FILE )
	args = parser.parse_args()
	
	return args


def main():
	args     = get_user_args()
	kml_path = Path( args.kml_file )
	if not kml_path.exists():
		raise FileNotFoundError( f"{args.kml_file} not found" )
	
	kml_content = kml_path.read_text( encoding="utf-8" )
	
	# Escape safely for embedding in JS template string
	kml_escaped = kml_content.replace( "`", "\\`" )
	
	# HTML template to _embed_ KML code because browser 
	# forbid loading from local resource
	#
	html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>OSM + Embedded KML</title>

  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

  <style>
    html, body {{
      height: 100%;
      margin: 0;
    }}
    #map {{
      width: 100%;
      height: 100%;
    }}
  </style>
</head>
<body>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet-omnivore@0.3.4/leaflet-omnivore.min.js"></script>

<script>
  const map = L.map('map').setView([52.52, 13.405], 12);

  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  const kmlData  = `{kml_escaped}`;
  const kmlLayer = omnivore.kml.parse( kmlData );
  const bounds   = kmlLayer.getBounds();
  map.fitBounds( bounds );
  kmlLayer.setStyle({{  // Omnivore KML does not implement <Style>
    color:       "#{TILE_COLOR_RGB}",
    fillColor:   "#{TILE_COLOR_RGB}",
    fillOpacity: {TILE_OPACITY}
  }});
  kmlLayer.addTo( map );

</script>
</body>
</html>
"""
	
	Path( args.htm_file ).write_text( html_content, encoding="utf-8" )
	print( f"Generated {args.htm_file}" )



if __name__ == "__main__":
	main()

