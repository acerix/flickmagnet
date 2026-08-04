

# Flick Magnet

Servidor HTTP para transmitir películas y programas de televisión de dominio público desde archivos torrent a tu navegador web.

## Captura de pantalla

![Flick Magnet 0.0.7 screenshot on desktop](https://acerix.github.io/flickmagnet/flickmagnet-0.0.7.png)

## Instalar el demonio

```
python3 setup.py install --optimize=1
```

## Iniciar el demonio

Instale examples/flickmagnet.service en systemd e inicie/active el servicio, o ejecute el flickmagnet.py instalado con python3:

```
python3 ./flickmagnet/flickmagnet.py
```

## Abrir en el navegador

Cuando se inicia el demonio, muestra una URL para conectarse desde los navegadores web. La URL predeterminada para conectarse a un demonio en la misma máquina es:

[http://localhost:42000/](http://localhost:42000/)
