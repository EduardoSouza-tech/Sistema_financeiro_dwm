# Script para remover caracteres acentuados e corrigir encoding
$file = "database_postgresql.py"
$content = Get-Content $file -Raw -Encoding UTF8

# Substituir caracteres corrompidos por equivalentes sem acento
$replacements = @{
    "á" = "a"; "à" = "a"; "ã" = "a"; "â" = "a"; "ä" = "a"
    "é" = "e"; "è" = "e"; "ê" = "e"; "ë" = "e"
    "í" = "i"; "ì" = "i"; "î" = "i"; "ï" = "i"
    "ó" = "o"; "ò" = "o"; "õ" = "o"; "ô" = "o"; "ö" = "o"
    "ú" = "u"; "ù" = "u"; "û" = "u"; "ü" = "u"
    "ç" = "c"
    "Á" = "A"; "À" = "A"; "Ã" = "A"; "Â" = "A"; "Ä" = "A"
    "É" = "E"; "È" = "E"; "Ê" = "E"; "Ë" = "E"
    "Í" = "I"; "Ì" = "I"; "Î" = "I"; "Ï" = "I"
    "Ó" = "O"; "Ò" = "O"; "Õ" = "O"; "Ô" = "O"; "Ö" = "O"
    "Ú" = "U"; "Ù" = "U"; "Û" = "U"; "Ü" = "U"
    "Ç" = "C"
    "ñ" = "n"; "Ñ" = "N"
    "ão" = "ao"; "ões" = "oes"; "õe" = "oe"
    "�" = "a"; "�" = "e"; "�" = "i"; "�" = "o"; "�" = "u"; "�" = "c"
}

foreach ($key in $replacements.Keys) {
    $content = $content -replace [regex]::Escape($key), $replacements[$key]
}

# Salvar com encoding UTF-8 sem BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($file, $content, $utf8NoBom)

Write-Host "Arquivo corrigido! Caracteres acentuados removidos."
