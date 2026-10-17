# Teste experimental: FSR 3.1 de 720p para 1080p

Base: tag oficial `windows-v2.4.0` (`7180a7b`). Objetivo de teste: GTX 1650 4 GB,
Ryzen 5 1400, 16 GB de RAM, CUSA01623 01.00. Ainda não validado nesse hardware/jogo.

Este teste reativa um caminho Vulkan já existente no projeto. Não implementa um
novo algoritmo FSR nem inclui geração de quadros. Não há promessa de ganho de FPS
ou de qualidade: o custo da reconstrução pode reduzir o desempenho de 720p.

## Executar

1. Guarde a instalação v2.4.0 que já funciona. Extraia o pacote de teste em outra
   pasta; use a mesma cópia do jogo. O teste não altera os arquivos do jogo.
2. Em Gráficos, marque **Testar FSR 3.1: 720p para 1080p** e clique em Salvar.
   A caixa fica desmarcada por padrão. A instalação de teste usa as configurações
   habituais do launcher; o perfil não altera a resolução interna salva.
3. Para a primeira comparação, use limite de 30 FPS e motor em 60 FPS. Mantenha
   o restante igual à instalação que funcionou, inclusive GPU e VSync.
4. Inicie o jogo. O perfil exige que o patch 720p seja aplicado por completo;
   se as assinaturas não coincidirem com o executável, ele encerra com uma mensagem.
   O nome CUSA01623/01.00, sozinho, não comprova compatibilidade das assinaturas.
5. No log (`user/last_run.log`, ou na pasta de saves personalizada), procure:

   ```text
   FSR 3.1 experiment: verified 720p patch; requesting 1280x720 -> 1920x1080
   Upscaler: FSR 3 context 1280x720 -> 1920x1080
   Upscaler: FSR 3.1 recorded first scaled dispatch: 1280x720 -> 1920x1080
   ```

   A primeira mensagem só confirma a configuração de inicialização. As outras
   confirmam a criação do contexto e o registro dos comandos de reconstrução,
   não a correção visual nem a conclusão dos comandos na GPU. Contexto sem dispatch,
   erros de dispatch ou dimensões diferentes precisam ser investigados.

6. Compare a mesma cena, depois de aquecer o cache: 720p normal, teste FSR com
   saída 1080p e 1080p nativo. Registre FPS, travadas, VRAM, detalhes em movimento,
   rastros em Kratos/armas, partículas e legibilidade do HUD. Para medir margem
   de desempenho, repita um trecho sem o limite de 30; restaure o limite depois.
7. Para voltar, feche o jogo, desmarque a caixa e salve. Não altere o provedor ou
   a resolução interna durante uma sessão experimental; reinicie pelo launcher.
   Não use o atualizador para substituir esta versão experimental.

## Como obter o pacote

Na branch `experimental/fsr-1080p`, o workflow **Windows zip** compila o código,
executa testes do launcher e verifica a abertura do pacote em Windows sem MSYS2.
Se concluir, o ZIP aparece em **Artifacts** na execução em Actions. Não publica
uma release automaticamente. Em um fork, Actions pode precisar ser habilitado.

Compilação local: siga `packaging/windows/README.md`, usando esta branch;
`bash build.sh` e `bash packaging/windows/package.sh`. O pacote fica em
`dist/gow3-windows`. Nenhum arquivo do jogo deve ser incluído no repositório.

## Próximas decisões

Se o caminho fixo não reconhecer os buffers da cena, primeiro corrigir a detecção.
Se houver rastros ou cintilação, investigar vetores de movimento, jitter e máscaras.
Se não mantiver 30 FPS, medir o custo por passe antes de acrescentar recursos.
Frame generation fica fora desta etapa.
