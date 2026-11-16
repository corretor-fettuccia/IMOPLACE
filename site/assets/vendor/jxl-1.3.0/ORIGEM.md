# Codificador JXL

Fonte: pacote npm **@jsquash/jxl 1.3.0**, projeto https://github.com/jamsinclair/jSquash .

`codec/enc/jxl_enc.js`, `codec/enc/jxl_enc.wasm`, `meta.js` e `utils.js` foram copiados do pacote, com sua licença Apache-2.0 em LICENSE. `codec.js` é um adaptador do Imoplace para inicialização single-thread e codificação sem perdas.

O encoder é hospedado junto ao site. O publicador utiliza `pillow-jxl-plugin 1.3.8` como decodificador independente, pois a comparação de pixels revelou arredondamentos no decoder WASM antigo. Esse decoder antigo não faz parte desta entrega.
