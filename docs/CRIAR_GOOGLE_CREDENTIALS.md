# Google Cloud — criar GOOGLE_CREDENTIALS para ler imagens do Drive

**Atenção:** `GOOGLE_CREDENTIALS` é um **JSON de conta de serviço**, não uma API Key genérica. O workflow atual usa `google-github-actions/auth@v2` com `credentials_json`.

## Passo a passo

1. Entre em https://console.cloud.google.com/ com a conta que administrará o projeto. Crie ou selecione um projeto, por exemplo `imoplace-drive`. Não confunda *ID de projeto* com *Script ID*.
2. Abra **APIs e serviços → Biblioteca** e habilite **Google Drive API** para esse projeto.
3. Abra **IAM e administrador → Contas de serviço → Criar conta de serviço**. Escolha um nome, por exemplo `imoplace-publicador`. Não é necessário conceder papéis administrativos amplos ao projeto para ler pastas compartilhadas.
4. Abra a conta criada, copie seu e-mail `...@...iam.gserviceaccount.com`. No Google Drive, compartilhe com esse e-mail a pasta que guarda as imagens do ImoPlace, com acesso de **Leitor**. Pastas em drives compartilhados podem exigir configuração distinta.
5. Na conta de serviço, abra **Chaves → Adicionar chave → Criar nova chave → JSON**. O navegador baixará um arquivo `.json`. Se a opção estiver bloqueada por política da organização, NÃO tente contornar; o projeto precisará migrar para autenticação sem chave (Workload Identity Federation), com mudanças no workflow.
6. No GitHub: `corretor-fettuccia/IMOPLACE` → Settings → Secrets and variables → Actions → **Secrets → New repository secret**. Nome exato `GOOGLE_CREDENTIALS`. No valor, cole o **conteúdo integral** do JSON, não o caminho nem o nome do arquivo.
7. Guarde o JSON fora do repositório, com acesso restrito, e execute o workflow sem reconstrução forçada inicialmente. Nunca cole esse conteúdo em chats, logs ou commits.

## Teste e problemas frequentes

- `GOOGLE_CREDENTIALS` ausente: secret cadastrado na aba errada ou não disponível ao job.
- Erro de JSON: conteúdo incompleto; recrie a credencial, sem divulgar seu conteúdo.
- HTTP 403 ao baixar WebP: a conta de serviço não tem permissão para ler o arquivo ou a pasta; verifique o compartilhamento no Drive.
- Se receber erro de permissão de criação de chave, prefira WIF; **não basta** usar uma API Key simples.
- Contas de serviço e Drive API geralmente podem ser usadas sem cobrança pela criação da credencial, sujeitos a quotas, políticas e eventual cobrança de outros serviços contratados. Verifique preços e quotas do Google Cloud no seu projeto.
