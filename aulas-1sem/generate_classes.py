import os

base_dir = "/Users/joseromualdocostafilho/Projects/FIAP/FIAP-2026-2-3SI/aulas-1sem"
aulas_dir = os.path.join(base_dir, "aulas")
labs_dir = os.path.join(base_dir, "labs")

os.makedirs(aulas_dir, exist_ok=True)
os.makedirs(labs_dir, exist_ok=True)

html_template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aula {num} – {title} | FIAP</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/monokai.css">
  <link rel="stylesheet" href="../assets/css/fiap-theme.css">
  <link rel="stylesheet" href="../assets/css/fiap-print.css">
  <script>if(/print-pdf/gi.test(window.location.search)){{var link=document.createElement('link');link.rel='stylesheet';link.href='https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/css/print/pdf.css';document.head.appendChild(link);}}</script>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
</head>
<body>
  <div class="reveal">
    <div class="slides">

      <!-- ==================== SLIDE: CAPA FIAP ==================== -->
      <section class="cover-slide">
        <img src="../assets/img/fiap-logo-graduacao.png" alt="FIAP Graduação" class="fiap-logo-full">
      </section>

      <!-- ==================== SLIDE: TÍTULO DA AULA ==================== -->
      <section class="title-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="title-card">
          <div class="accent-bar"></div>
          <h1>Sistemas de Informação</h1>
          <h2>Microservice and Web Engineering & IT Services</h2>
          <h3>Prof. José Romualdo</h3>
        </div>
        <div class="lesson-bar">AULA {num} – {title}</div>
      </section>

      <!-- ==================== SLIDE: AGENDA ==================== -->
      <section class="content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>Agenda do Encontro</h2>
        </div>

        <table>
          <thead>
            <tr><th>Bloco</th><th>Horário</th><th>Conteúdo & Atividades</th></tr>
          </thead>
          <tbody>
            <tr><td><strong>Bloco 1</strong></td><td>19h20 – 20h50</td><td>{bloco1_content}</td></tr>
            <tr><td><strong>Intervalo</strong></td><td>20h50 – 21h20</td><td>☕ Pausa para Café e Networking (30 min)</td></tr>
            <tr><td><strong>Bloco 2</strong></td><td>21h20 – 22h50</td><td>{bloco2_content}</td></tr>
          </tbody>
        </table>

        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">3</div>
        </div>
      </section>

      <!-- ==================== SLIDE: CONTEÚDO 1 ==================== -->
      <section class="content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>{topic1_title}</h2>
        </div>
        <div class="concept-cards">
          {topic1_cards}
        </div>
        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">4</div>
        </div>
      </section>

      <!-- ==================== SLIDE: QUIZ 1 ==================== -->
      <section class="quiz-slide content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>Quiz #1 (Fixação do Bloco 1)</h2>
        </div>
        <div class="quiz-container">
          <div class="quiz-question">{q1_q}</div>
          <ul class="quiz-options">
            {q1_options}
          </ul>
          <div class="quiz-feedback" data-correct-msg="{q1_c}" data-incorrect-msg="{q1_i}"></div>
        </div>
        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">5</div>
        </div>
      </section>

      <!-- ==================== SLIDE: PAUSA ==================== -->
      <section class="content-slide" style="text-align:center;">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div style="margin-top:100px;">
          <h2 style="font-size:2.5em; color:var(--fiap-pink);">☕ Pausa para Café</h2>
          <h3 style="font-size:1.5em; color:var(--fiap-gray-light); margin-top:20px;">20h50 – 21h20 (30 minutos)</h3>
          <p style="margin-top:40px; font-size:1.1em;">Na volta: Quizzes #2 e #3 + Hands-on Lab!</p>
        </div>
        <div class="slide-footer"><div class="footer-page">6</div></div>
      </section>

      <!-- ==================== SLIDE: QUIZ 2 ==================== -->
      <section class="quiz-slide content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>Quiz #2 (Retorno do Intervalo)</h2>
        </div>
        <div class="quiz-container">
          <div class="quiz-question">{q2_q}</div>
          <ul class="quiz-options">
            {q2_options}
          </ul>
          <div class="quiz-feedback" data-correct-msg="{q2_c}" data-incorrect-msg="{q2_i}"></div>
        </div>
        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">7</div>
        </div>
      </section>

      <!-- ==================== SLIDE: QUIZ 3 ==================== -->
      <section class="quiz-slide content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>Quiz #3</h2>
        </div>
        <div class="quiz-container">
          <div class="quiz-question">{q3_q}</div>
          <ul class="quiz-options">
            {q3_options}
          </ul>
          <div class="quiz-feedback" data-correct-msg="{q3_c}" data-incorrect-msg="{q3_i}"></div>
        </div>
        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">8</div>
        </div>
      </section>

      <!-- ==================== SLIDE: HANDS-ON LAB ==================== -->
      <section class="content-slide">
        <div class="top-bar"></div>
        <img src="../assets/img/fiap-logo-simple.png" alt="FIAP" class="fiap-logo-header">
        <div class="slide-title-area">
          <div class="accent-bar"></div>
          <h2>Hands-on Lab: LogiTech Enterprise</h2>
        </div>
        <div class="concept-cards">
          <div class="concept-card">
            <h4>Missão</h4>
            <p>{lab_mission}</p>
          </div>
          <div class="concept-card">
            <h4>Passo a Passo</h4>
            <p>{lab_steps}</p>
          </div>
        </div>
        <pre><code class="language-{lab_lang}">{lab_code}</code></pre>
        <div class="slide-footer">
          <div class="footer-bar">{num} – {short_title}</div>
          <div class="footer-page">9</div>
        </div>
      </section>

      <!-- ==================== SLIDE: ENCERRAMENTO ==================== -->
      <section class="end-slide">
        <img src="../assets/img/fiap-logo-graduacao.png" alt="FIAP Graduação" style="max-width:350px;">
        <div class="copyright">
          Copyright &copy; 2026<br>
          Prof.º José Romualdo da Costa Filho<br><br>
          Todos direitos reservados. Reprodução ou divulgação total ou parcial<br>
          deste documento é expressamente proibido sem o consentimento formal,<br>
          por escrito, do Professor (autor).
        </div>
      </section>

    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
  <script src="../assets/js/fiap-quiz.js"></script>
  <script>
    Reveal.initialize({{
      hash: true,
      slideNumber: false,
      width: 1280,
      height: 720,
      margin: 0,
      minScale: 0.2,
      maxScale: 2.0,
      center: false,
      pdfMaxPagesPerSlide: 1,
      pdfSeparateFragments: false,
      transition: 'slide',
      transitionSpeed: 'default',
      plugins: [RevealHighlight]
    }});
  </script>
</body>
</html>
"""

classes = [
    {
        "num": "02",
        "title": "HTTP/1.1 a 3, SSE, Wireshark & Git Branching",
        "short_title": "HTTP, SSE & Git",
        "bloco1_content": "Evolução do HTTP + SSE (Server-Sent Events) + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + Hands-on Lab (SSE App) + Git Branching",
        "topic1_title": "Evolução HTTP & SSE (Server-Sent Events)",
        "topic1_cards": '''<div class="concept-card"><h4>HTTP/1.1 a 3</h4><p>HTTP/1.1 (Keep-Alive), HTTP/2 (Multiplexação) e HTTP/3 (QUIC / UDP).</p></div>
                         <div class="concept-card"><h4>SSE (Server-Sent Events)</h4><p>Comunicação unidirecional Servidor -> Cliente sobre HTTP. Excelente para atualizações em tempo real.</p></div>''',
        "q1_q": "Qual a principal melhoria do HTTP/2 em relação ao HTTP/1.1?",
        "q1_options": '''<li data-correct="false"><span class="option-letter">A</span>Migração exclusiva para UDP.</li>
                         <li data-correct="true"><span class="option-letter">B</span>Multiplexação de várias requisições em uma única conexão TCP.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Criação do método GET.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Fim do uso de certificados TLS.</li>''',
        "q1_c": "Correto! A multiplexação resolve o Head-of-Line Blocking do HTTP/1.1.",
        "q1_i": "Atenção: A grande inovação do HTTP/2 foi a multiplexação em uma mesma conexão TCP.",
        
        "q2_q": "Sobre o Server-Sent Events (SSE), assinale a alternativa correta:",
        "q2_options": '''<li data-correct="false"><span class="option-letter">A</span>É um protocolo bidirecional, substituindo os WebSockets completamente.</li>
                         <li data-correct="true"><span class="option-letter">B</span>É unidirecional (Servidor -> Cliente), ideal para feeds de notícias e notificações.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Funciona apenas na porta 443 sem uso do HTTP.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Não suporta reconexão automática.</li>''',
        "q2_c": "Perfeito! SSE usa HTTP padrão e entrega eventos unidirecionais do servidor.",
        "q2_i": "Erro! SSE é unidirecional e constrói sobre HTTP.",
        
        "q3_q": "No Git, o que o comando 'git branch' faz?",
        "q3_options": '''<li data-correct="true"><span class="option-letter">A</span>Lista, cria ou deleta ramificações no repositório.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Envia o código para o servidor remoto.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Desfaz o último commit.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Apaga permanentemente o histórico.</li>''',
        "q3_c": "Exato! Branches isolam o desenvolvimento de novas features.",
        "q3_i": "Incorreto. Git branch gerencia as linhas de desenvolvimento.",
        
        "lab_mission": "Implementar um servidor Node.js que envia atualizações de entrega da LogiTech via SSE.",
        "lab_steps": "1. Criar branch `feature/sse-tracking`<br>2. Escrever `server.js`<br>3. Commit e merge.",
        "lab_lang": "javascript",
        "lab_code": """// server.js
const http = require('http');

http.createServer((req, res) => {
  if (req.url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });
    setInterval(() => {
      res.write(`data: ${JSON.stringify({ status: 'Em trânsito', lat: -23.5, lng: -46.6 })}\\n\\n`);
    }, 2000);
  }
}).listen(3000, () => console.log('SSE Server na porta 3000'));"""
    },
    {
        "num": "03",
        "title": "Docker I (Dockerfile Multi-Stage, Volumes & Networks)",
        "short_title": "Docker I",
        "bloco1_content": "Fundamentos Docker, Dockerfile Multi-Stage + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + Volumes & Networks + Hands-on Lab",
        "topic1_title": "Isolamento com Docker",
        "topic1_cards": '''<div class="concept-card"><h4>Multi-Stage Builds</h4><p>Técnica para criar imagens Docker leves, separando o build da execução.</p></div>
                         <div class="concept-card"><h4>Volumes & Networks</h4><p>Persistência de dados (Volumes) e comunicação isolada entre containers (Networks).</p></div>''',
        "q1_q": "Qual a principal vantagem do Dockerfile Multi-Stage?",
        "q1_options": '''<li data-correct="true"><span class="option-letter">A</span>Reduzir o tamanho da imagem final mantendo apenas os artefatos necessários.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Permitir rodar múltiplos containers no mesmo Dockerfile.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Forçar o uso de Kubernetes.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Aumentar a segurança trocando a senha do root.</li>''',
        "q1_c": "Exato! Descartamos as ferramentas de build e levamos só o executável/artefato.",
        "q1_i": "Errado. Multi-stage foca em diminuir a imagem final.",
        
        "q2_q": "Como garantimos que os dados de um banco de dados não se percam ao remover o container?",
        "q2_options": '''<li data-correct="false"><span class="option-letter">A</span>Usando docker commit a cada segundo.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Escrevendo logs no stdout.</li>
                         <li data-correct="true"><span class="option-letter">C</span>Mapeando um Docker Volume ou Bind Mount para a pasta de dados.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Não é possível, Docker é 100% efêmero.</li>''',
        "q2_c": "Certo! Volumes mantêm o ciclo de vida dos dados independente do container.",
        "q2_i": "Cuidado, volumes e bind mounts são as estratégias corretas de persistência.",
        
        "q3_q": "Qual comando cria uma rede isolada para nossos microserviços?",
        "q3_options": '''<li data-correct="true"><span class="option-letter">A</span>docker network create minha-rede</li>
                         <li data-correct="false"><span class="option-letter">B</span>docker build --network</li>
                         <li data-correct="false"><span class="option-letter">C</span>docker compose up</li>
                         <li data-correct="false"><span class="option-letter">D</span>ipconfig /all</li>''',
        "q3_c": "Correto! Isso permite que containers se comuniquem via DNS interno.",
        "q3_i": "Incorreto. A criação manual usa `docker network create`.",
        
        "lab_mission": "Criar um Dockerfile Multi-Stage para uma API Python (LogiTech).",
        "lab_steps": "1. Analisar app.py<br>2. Construir Dockerfile com estágio de build e runtime<br>3. Rodar e testar.",
        "lab_lang": "dockerfile",
        "lab_code": """# Dockerfile
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]"""
    },
    {
        "num": "05",
        "title": "POO, SOLID & Design Patterns em Java (Spring Boot) & C# (.NET Core)",
        "short_title": "SOLID & Patterns",
        "bloco1_content": "Princípios SOLID + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + Design Patterns Factory & Strategy + Lab",
        "topic1_title": "Código Limpo e Escalável",
        "topic1_cards": '''<div class="concept-card"><h4>SOLID</h4><p>SRP, OCP, LSP, ISP e DIP. Pilares da POO moderna.</p></div>
                         <div class="concept-card"><h4>Strategy Pattern</h4><p>Encapsula algoritmos (ex: cálculo de frete) tornando-os intercambiáveis.</p></div>''',
        "q1_q": "O Princípio do Aberto/Fechado (OCP) diz que uma entidade de software deve estar:",
        "q1_options": '''<li data-correct="false"><span class="option-letter">A</span>Aberta para modificação, mas fechada para extensão.</li>
                         <li data-correct="true"><span class="option-letter">B</span>Aberta para extensão, mas fechada para modificação.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Fechada para testes, aberta para deploy.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Aberta para uso público, fechada para privado.</li>''',
        "q1_c": "Perfeito! Você adiciona novos comportamentos (extensão) sem alterar código existente (modificação).",
        "q1_i": "Reveja o OCP. O foco é estender sem quebrar o que já existe.",
        
        "q2_q": "Qual a principal vantagem do padrão Strategy?",
        "q2_options": '''<li data-correct="true"><span class="option-letter">A</span>Eliminar grandes blocos de if/else delegando o comportamento para classes específicas.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Garantir que apenas uma instância da classe exista (Singleton).</li>
                         <li data-correct="false"><span class="option-letter">C</span>Adaptar uma interface velha para uma nova.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Aumentar a performance de processamento do banco de dados.</li>''',
        "q2_c": "Exato! Strategy favorece a composição e o Open/Closed Principle.",
        "q2_i": "Errado. Strategy é comportamental e substitui condicionais complexas.",
        
        "q3_q": "Em Spring Boot ou .NET Core, como aplicamos a Inversão de Dependência (DIP)?",
        "q3_options": '''<li data-correct="true"><span class="option-letter">A</span>Injetando dependências via construtor (Injeção de Dependência).</li>
                         <li data-correct="false"><span class="option-letter">B</span>Herdando de classes base abstratas infinitamente.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Usando 'new' dentro de todos os métodos.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Criando variáveis globais estáticas.</li>''',
        "q3_c": "Isso aí! O framework gerencia o ciclo de vida (IoC Container).",
        "q3_i": "O DIP é implementado através da Injeção de Dependência nos frameworks modernos.",
        
        "lab_mission": "Implementar Strategy para Cálculo de Frete (LogiTech) em Java ou C#.",
        "lab_steps": "1. Criar interface `FreightStrategy`<br>2. Implementar `Sedex` e `PAC`<br>3. Usar Injeção de Dependência.",
        "lab_lang": "java",
        "lab_code": """// Java (Spring) Example
public interface FreightStrategy {
    double calculate(double distance);
}

@Service
public class SedexStrategy implements FreightStrategy {
    public double calculate(double distance) {
        return distance * 1.5;
    }
}

@Service
public class FreightService {
    private final Map<String, FreightStrategy> strategies;
    // Constructor injection
    public FreightService(Map<String, FreightStrategy> strategies) {
        this.strategies = strategies;
    }
}"""
    },
    {
        "num": "06",
        "title": "Design Patterns (Adapter, Decorator, Strategy) & APIs em Node.js (TypeScript) & Python (FastAPI)",
        "short_title": "APIs & Patterns",
        "bloco1_content": "Adapter & Decorator em Python e TypeScript + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + Criação de API (FastAPI / Express) + Lab",
        "topic1_title": "Padrões Estruturais em APIs",
        "topic1_cards": '''<div class="concept-card"><h4>Adapter</h4><p>Conecta interfaces incompatíveis. Útil para integrar APIs de terceiros (ex: legado).</p></div>
                         <div class="concept-card"><h4>Decorator</h4><p>Adiciona comportamentos a objetos dinamicamente sem alterar a classe (ex: Middlewares, anotações de rota).</p></div>''',
        "q1_q": "Qual é a função do padrão Decorator?",
        "q1_options": '''<li data-correct="false"><span class="option-letter">A</span>Instanciar objetos de forma controlada.</li>
                         <li data-correct="true"><span class="option-letter">B</span>Adicionar responsabilidades adicionais a um objeto dinamicamente.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Prover uma interface simplificada para um subsistema complexo.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Traduzir uma classe para outra.</li>''',
        "q1_c": "Correto! Ele 'abraça' a função/classe original e adiciona comportamento (como os @decorators do Python).",
        "q1_i": "Atenção: O Decorator anexa responsabilidades extras sem alterar a estrutura base.",
        
        "q2_q": "Ao integrar a LogiTech com a API dos Correios (SOAP antigo) para o nosso sistema REST moderno, qual padrão usar?",
        "q2_options": '''<li data-correct="false"><span class="option-letter">A</span>Singleton</li>
                         <li data-correct="true"><span class="option-letter">B</span>Adapter</li>
                         <li data-correct="false"><span class="option-letter">C</span>Observer</li>
                         <li data-correct="false"><span class="option-letter">D</span>Factory</li>''',
        "q2_c": "Perfeito! O Adapter 'traduz' as chamadas do nosso domínio para o domínio externo.",
        "q2_i": "Pense num adaptador de tomada: ele conecta interfaces incompatíveis. Padrão Adapter.",
        
        "q3_q": "No FastAPI, o que representa a notação @app.get('/rota')?",
        "q3_options": '''<li data-correct="true"><span class="option-letter">A</span>Um Decorator que mapeia a URL para a função.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Um Strategy que injeta um banco de dados.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Uma herança múltipla.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Um erro de sintaxe do Python.</li>''',
        "q3_c": "Exato! Decorators em Python são amplamente usados em web frameworks.",
        "q3_i": "Isso é um decorator Python! Adiciona comportamento de roteamento.",
        
        "lab_mission": "Criar uma API FastAPI usando Adapter para um serviço falso de tracking.",
        "lab_steps": "1. Criar `main.py`<br>2. Definir a classe Adapter<br>3. Expor um endpoint GET.",
        "lab_lang": "python",
        "lab_code": """# main.py (FastAPI)
from fastapi import FastAPI

app = FastAPI()

class LegacyTrackingAPI:
    def get_status(self, code: str) -> str:
        return "ENTREGUE_LEGADO"

class TrackingAdapter:
    def __init__(self, legacy: LegacyTrackingAPI):
        self.legacy = legacy
    
    def track(self, code: str) -> dict:
        status = self.legacy.get_status(code)
        return {"code": code, "status": status.lower(), "modern": True}

@app.get("/track/{code}")
def track_order(code: str):
    adapter = TrackingAdapter(LegacyTrackingAPI())
    return adapter.track(code)
"""
    },
    {
        "num": "07",
        "title": "Docker Compose Multi-Serviço & AI Gateways (Strategy/Facade Patterns)",
        "short_title": "Compose & Gateways",
        "bloco1_content": "Docker Compose, Volumes, Network + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + AI Gateways (Facade) + Lab",
        "topic1_title": "Orquestração Local & AI Gateways",
        "topic1_cards": '''<div class="concept-card"><h4>Docker Compose</h4><p>Ferramenta para definir e rodar aplicações multi-container usando YAML.</p></div>
                         <div class="concept-card"><h4>AI Gateway / Facade</h4><p>Uma interface única que abstrai chamadas para múltiplos LLMs (OpenAI, Gemini, etc).</p></div>''',
        "q1_q": "Qual arquivo é usado por padrão para configurar o Docker Compose?",
        "q1_options": '''<li data-correct="true"><span class="option-letter">A</span>docker-compose.yml</li>
                         <li data-correct="false"><span class="option-letter">B</span>Dockerfile</li>
                         <li data-correct="false"><span class="option-letter">C</span>package.json</li>
                         <li data-correct="false"><span class="option-letter">D</span>Makefile</li>''',
        "q1_c": "Isso mesmo! O manifesto YAML define os serviços, redes e volumes.",
        "q1_i": "Lembre-se: Compose usa arquivos .yml ou .yaml.",
        
        "q2_q": "O padrão Facade (Fachada) é aplicado em um AI Gateway para:",
        "q2_options": '''<li data-correct="true"><span class="option-letter">A</span>Esconder a complexidade das múltiplas APIs de IA por trás de uma única interface simples.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Aumentar a complexidade do cliente.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Substituir o uso de Docker no backend.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Proibir o uso de Inteligência Artificial.</li>''',
        "q2_c": "Exato! O Facade simplifica o consumo (um único endpoint que roteia para o LLM correto).",
        "q2_i": "O objetivo do Facade é justamente esconder a complexidade.",
        
        "q3_q": "Como os serviços dentro do mesmo Docker Compose se comunicam?",
        "q3_options": '''<li data-correct="false"><span class="option-letter">A</span>Através de chamadas HTTPS para a internet pública.</li>
                         <li data-correct="true"><span class="option-letter">B</span>Através dos nomes dos serviços, que funcionam como DNS numa rede interna.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Lendo e escrevendo no mesmo disco rígido.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Não se comunicam.</li>''',
        "q3_c": "Perfeito! O Docker embutiu um servidor DNS que resolve o nome do serviço para o IP do container.",
        "q3_i": "No compose, a resolução de nomes é automática usando o nome do serviço (DNS).",
        
        "lab_mission": "Subir uma infraestrutura completa (API + Redis) e criar um Facade para IA.",
        "lab_steps": "1. Criar `docker-compose.yml`<br>2. Definir o serviço web e redis<br>3. `docker compose up -d`.",
        "lab_lang": "yaml",
        "lab_code": """# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
  redis:
    image: "redis:alpine"
    ports:
      - "6379:6379"
"""
    },
    {
        "num": "08",
        "title": "Orquestração de Agentes (Command Pattern / Function Calling) & Git Worktrees I",
        "short_title": "Agentes & Worktrees",
        "bloco1_content": "LLM Function Calling + Command Pattern + Quiz #1",
        "bloco2_content": "Quizzes #2 e #3 + Git Worktrees + Lab Agentes",
        "topic1_title": "LLMs como Agentes (Function Calling)",
        "topic1_cards": '''<div class="concept-card"><h4>Function Calling</h4><p>Capacidade de um LLM de decidir quando e com quais parâmetros chamar uma função determinística (ferramenta).</p></div>
                         <div class="concept-card"><h4>Git Worktree</h4><p>Trabalhar em múltiplas branches simultaneamente em diretórios separados, sem precisar de stashes frequentes.</p></div>''',
        "q1_q": "No contexto de Agentes IA, o que é o Function Calling?",
        "q1_options": '''<li data-correct="false"><span class="option-letter">A</span>Uma função que chama a si mesma recursivamente.</li>
                         <li data-correct="true"><span class="option-letter">B</span>A IA retorna um JSON estruturado com os dados para o sistema invocar uma API ou função local.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Um telefone físico para suporte.</li>
                         <li data-correct="false"><span class="option-letter">D</span>A IA executa o código diretamente no núcleo do sistema operacional.</li>''',
        "q1_c": "Certo! O LLM não executa; ele infere a intenção e os argumentos, e nosso código executa.",
        "q1_i": "O LLM apenas sugere a assinatura e os argumentos; o sistema invoca a função.",
        
        "q2_q": "Qual Design Pattern melhor representa a abstração de uma ferramenta (Tool) para um Agente IA?",
        "q2_options": '''<li data-correct="false"><span class="option-letter">A</span>Singleton</li>
                         <li data-correct="false"><span class="option-letter">B</span>Observer</li>
                         <li data-correct="true"><span class="option-letter">C</span>Command Pattern</li>
                         <li data-correct="false"><span class="option-letter">D</span>Flyweight</li>''',
        "q2_c": "Exato! O Command encapsula a ação e seus argumentos como um objeto executável (execute()).",
        "q2_i": "Command encapsula uma requisição como um objeto (a ferramenta/função).",
        
        "q3_q": "O comando 'git worktree add' serve para:",
        "q3_options": '''<li data-correct="true"><span class="option-letter">A</span>Fazer checkout de uma branch em uma pasta separada, mantendo o mesmo repositório local.</li>
                         <li data-correct="false"><span class="option-letter">B</span>Adicionar um novo repositório remoto.</li>
                         <li data-correct="false"><span class="option-letter">C</span>Criar um arquivo zip do projeto.</li>
                         <li data-correct="false"><span class="option-letter">D</span>Deletar arquivos temporários.</li>''',
        "q3_c": "Perfeito! Muito útil para revisar um PR urgente sem perder o contexto atual.",
        "q3_i": "Worktree permite múltiplas branches em diretórios físicos diferentes.",
        
        "lab_mission": "Implementar o Command Pattern simulando as ferramentas de um Agente IA de Logística.",
        "lab_steps": "1. Criar interface `ToolCommand`<br>2. Implementar `RastrearPedidoCommand`<br>3. Invocar baseado no JSON simulado.",
        "lab_lang": "python",
        "lab_code": """# agent.py
class Command:
    def execute(self, **kwargs):
        pass

class RastrearPedido(Command):
    def execute(self, **kwargs):
        pedido_id = kwargs.get("pedido_id")
        return f"Pedido {pedido_id} está em transito."

# Simulando resposta do LLM
llm_response = {
    "tool": "rastrear",
    "args": {"pedido_id": "LOG-1234"}
}

tools = {"rastrear": RastrearPedido()}
comando = tools.get(llm_response["tool"])
if comando:
    print(comando.execute(**llm_response["args"]))
"""
    }
]

import json

for c in classes:
    # Build HTML
    html_content = html_template.format(**c)
    html_path = os.path.join(aulas_dir, f"aula{c['num']}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Build Labs
    lab_folder = os.path.join(labs_dir, f"aula{c['num']}-lab")
    os.makedirs(lab_folder, exist_ok=True)
    
    # Dump lab files depending on the class
    if c['num'] == "02":
        with open(os.path.join(lab_folder, "server.js"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 02 - Lab SSE\\n\\nExecute `node server.js` e consuma a rota `/events`.")
    elif c['num'] == "03":
        with open(os.path.join(lab_folder, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        with open(os.path.join(lab_folder, "app.py"), "w", encoding="utf-8") as f:
            f.write("print('Hello from LogiTech')\\n")
        with open(os.path.join(lab_folder, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("requests==2.31.0\\n")
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 03 - Docker Multi-Stage\\n\\nExecute `docker build -t logitech-api .` e depois `docker run logitech-api`.")
    elif c['num'] == "05":
        java_dir = os.path.join(lab_folder, "java")
        csharp_dir = os.path.join(lab_folder, "csharp")
        os.makedirs(java_dir, exist_ok=True)
        os.makedirs(csharp_dir, exist_ok=True)
        with open(os.path.join(java_dir, "FreightStrategy.java"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        with open(os.path.join(csharp_dir, "FreightStrategy.cs"), "w", encoding="utf-8") as f:
            f.write("// C# implementation of FreightStrategy\\npublic interface IFreightStrategy { double Calculate(double distance); }")
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 05 - SOLID & Design Patterns\\n\\nLaboratório demonstrando injeção de dependência e Strategy pattern em Java e C#.")
    elif c['num'] == "06":
        py_dir = os.path.join(lab_folder, "python-fastapi")
        ts_dir = os.path.join(lab_folder, "node-ts")
        os.makedirs(py_dir, exist_ok=True)
        os.makedirs(ts_dir, exist_ok=True)
        with open(os.path.join(py_dir, "main.py"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        with open(os.path.join(ts_dir, "api.ts"), "w", encoding="utf-8") as f:
            f.write("// TypeScript Adapter Pattern stub\\nclass Adapter { }")
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 06 - Adapter e Decorator\\n\\nLabs em Python FastAPI e Node/TypeScript.")
    elif c['num'] == "07":
        with open(os.path.join(lab_folder, "docker-compose.yml"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        os.makedirs(os.path.join(lab_folder, "gateway"), exist_ok=True)
        with open(os.path.join(lab_folder, "gateway", "app.py"), "w", encoding="utf-8") as f:
            f.write("from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/')\\ndef proxy(): return {'status': 'Facade API'}\\n")
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 07 - Docker Compose e AI Gateway\\n\\nExecute `docker-compose up`.")
    elif c['num'] == "08":
        with open(os.path.join(lab_folder, "agent.py"), "w", encoding="utf-8") as f:
            f.write(c['lab_code'])
        with open(os.path.join(lab_folder, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Aula 08 - Agentes e Function Calling\\n\\nExecute `python agent.py`.")

print("All classes and labs generated successfully.")
