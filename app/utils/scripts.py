def open_window_script(url, width, height):
    command = f"window.open('{url}', '_blank', `width={width},height={height},toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes`);"
    return f"<script>{command}</script>"

