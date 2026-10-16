# CORPO-OBJETIVO-01 / CORPO-VARIANTE-01 — 13/10/2026

Pedido: aplicar continuidade entre turnos e planejamento corporal mais adaptável,
enquanto Pedro busca sensores. A aplicação deve permanecer fechada ao final.
Não se conhece ainda modelo/interface dos sensores; nenhum sensor foi integrado.
Nenhum movimento físico foi comandado neste incremento.

Base main, d850b8c90cc5ce40bd4832e759ed991ba88cd5cc; alterações paralelas
preservadas. Cinco módulos centrais congelados em baseline/, status e HEAD
registrados. Nenhum commit, configuração ou firmware alterado.

## Fronteiras e contratos

O codec da autoria corporal só aceitava nome; não havia uma referência atual
ao objetivo anterior. Assim, o owner sempre iniciava outro objetivo no turno
novo. REDs alcançaram publicação canônica, ausência da referência e seleção
indiferente à repetição factual. São fronteiras distintas, com provas próprias.

Ampliação localizada do contrato principal: nome + objetivo_id opcional.
Referência só pode apontar ao retrato de um objetivo vivo do owner, na mesma
concessão/sessão, com validade fixa de 120 s e no máximo oito turnos. O prazo
não é renovado. O novo turno tem proposta/identidade e validações próprias;
nenhuma coreografia, autorização ou receipt antigo é herdado. O nome antigo
continua compatível. Não há parser de frases privado ou segunda chamada à IA
para decidir a continuidade; a autoria principal existente propõe o vínculo.

Corrida reproduzida: atenção durante espera da LLM substituía a intenção e
perdia o candidato anterior. O owner mantém uma referência observacional
limitada durante essa espera. O retrato anterior ou recapturado conserva a
referência; ela não arma motores. Nova proposta pode aceitá-la; assunto novo
omite o vínculo. Descansar explícito/revogação encerra o objetivo e idle não
o reativa. Turno/plano novo continua interrompendo o gesto já iniciado.

O objetivo conserva contexto textual de origem, com fonte/turno, para a mente
comparar o propósito atual ao anterior. Esse contexto é descritivo e limitado;
não concede autorização nem resolve alvos de outras capacidades.

Planejamento: seleção de variantes usa os seis registros mais recentes da
experiência compartilhada, filtrando família/perfil/sessão, confirmação elétrica
ou execução parcial, e descartando registros recuperados de sessões antigas.
Reduz repetição imediata e frequência sem mudar partituras/PWM/limites.
Preferências maduras continuam prevalecendo, recusas maduras excluem variantes,
e nenhuma preferência concede movimento. Não é planejamento de trajetória nem
calibração de distância/ângulo.

## Autoria e transporte

Primeiro ensaio real: nome interagir válido, objetivo_id omitido. Candidato de
instrução excedeu o transporte local (4255 caracteres no contexto mínimo).
O teste não foi enfraquecido. Instrução foi compactada preservando contratos;
projeção omite somente história opcional para caber em 3800 caracteres, sem
cortar condição atual, referência ou regras de saída. Indica histórico omitido.

Outra amostra vinculou conversa, mas herdou objetivo na mudança de assunto.
Artefato RED preservado. Hipótese de propósito insuficiente: referência só
nomeava interagir, sem contexto de origem; esse nome também serve a um assunto
independente. Incluído contexto factual e exemplos distintos para continuidade
e assunto novo. Não há reparo de objetivo_id depois da geração.

Consulta final com modelo configurado + USB/composição reais vinculou objetivo
na continuação e omitiu a referência na pergunta independente de aritmética.
JSON e publicação principal validados. Instruções de 3699/3695 caracteres.
Nenhuma proposta foi executada; SerialSemMotor rejeita qualquer MOTOR antes
do write. GOODNIGHT/encerramento enviados pelo owner existente ao final.
receipt_sem_motor_primeiro.json e receipt_sem_motor_assunto_red.json preservam
falhas; receipt_sem_motor.json registra a última consulta.

Isso é prova amostral de acesso/autoria/vínculo, não garantia de interpretação
correta em toda conversa. Uso físico e apreciação humana ainda pendentes.

## Validação e limites

19 testes novos: referências, corrida da espera, expiração/revogação/sessão,
mudança de assunto, limite fixo e oito turnos, encerramento, histórico, catálogo,
cooperação, ausência de replay e composição instalada. Retrato povoado com
histórico passa inteiro pelo preparador e compactador reais.

Seleção final: 170 verdes/um caso de receipt instalado deselecionado após
controle de baseline; decisão isolada: 14 verdes. Contagens em focado_final.txt
e decisao_final.txt. Regressão
ampla inicial NÃO foi toda verde: registro/receipt legado de comando instalado
falhou em corpo/música. Dois controles também falharam carregando os cinco
módulos congelados no início, sem editar produção (regressao_baseline.txt).
Esse controle falsifica que a falha desses casos tenha sido causada pelo novo
vínculo ou seleção; não declara a causa real dessa raiz paralela. Testes e
falhas amplos foram preservados, sem enfraquecer expectations de receipt.

Produção deste incremento: modelo_corporal.py, companhia_corporal.py,
corpo_motor_runtime.py, experiencia_corporal_runtime.py e mapa_habilidades.py.
Shared state, aprendizagem/SQLite, contrato principal, coordenação e gates de
execução existentes reutilizados. Firmware/sono/bip e configuração preservados.
Nenhuma interface foi aberta na sonda; aplicação normal permanece fechada.
