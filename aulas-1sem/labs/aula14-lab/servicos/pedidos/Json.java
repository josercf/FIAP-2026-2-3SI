// LogiTech Enterprise - leitor e escritor de JSON minimo, sem dependencia.
//
// CONGELADO: nao e tarefa do laboratorio.
//
// Existe porque este servico compila com `javac` puro, sem Maven e sem
// baixar biblioteca nenhuma da rede. Num projeto real voce usaria Jackson.
// Aqui, ler o parser inteiro custa cinco minutos e evita que a aula dependa
// de um repositorio de artefatos responder.
//
// Cobre o subconjunto de JSON que aparece num JWT e num JWKS: objeto, lista,
// string com escape, numero, true, false, null.

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Json {

    private final String texto;
    private int i;

    private Json(String texto) {
        this.texto = texto;
    }

    /** Le um documento JSON e devolve Map, List, String, Double, Boolean ou null. */
    public static Object ler(String texto) {
        Json j = new Json(texto);
        j.espacos();
        Object valor = j.valor();
        j.espacos();
        if (j.i < texto.length()) {
            throw new IllegalArgumentException("sobrou texto depois do JSON, na posicao " + j.i);
        }
        return valor;
    }

    /** Atalho tipado para o caso mais comum: o documento e um objeto. */
    @SuppressWarnings("unchecked")
    public static Map<String, Object> lerObjeto(String texto) {
        Object v = ler(texto);
        if (!(v instanceof Map)) {
            throw new IllegalArgumentException("esperava um objeto JSON, veio " + v);
        }
        return (Map<String, Object>) v;
    }

    // -----------------------------------------------------------------
    // Escrita
    // -----------------------------------------------------------------

    public static String escrever(Object valor) {
        StringBuilder sb = new StringBuilder();
        escrever(valor, sb);
        return sb.toString();
    }

    private static void escrever(Object valor, StringBuilder sb) {
        if (valor == null) {
            sb.append("null");
        } else if (valor instanceof String) {
            texto((String) valor, sb);
        } else if (valor instanceof Number || valor instanceof Boolean) {
            sb.append(valor);
        } else if (valor instanceof Map) {
            sb.append('{');
            boolean primeiro = true;
            for (Map.Entry<?, ?> e : ((Map<?, ?>) valor).entrySet()) {
                if (!primeiro) sb.append(',');
                primeiro = false;
                texto(String.valueOf(e.getKey()), sb);
                sb.append(':');
                escrever(e.getValue(), sb);
            }
            sb.append('}');
        } else if (valor instanceof Iterable) {
            sb.append('[');
            boolean primeiro = true;
            for (Object o : (Iterable<?>) valor) {
                if (!primeiro) sb.append(',');
                primeiro = false;
                escrever(o, sb);
            }
            sb.append(']');
        } else {
            texto(String.valueOf(valor), sb);
        }
    }

    private static void texto(String s, StringBuilder sb) {
        sb.append('"');
        for (int k = 0; k < s.length(); k++) {
            char c = s.charAt(k);
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default:
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c));
                    else sb.append(c);
            }
        }
        sb.append('"');
    }

    // -----------------------------------------------------------------
    // Leitura
    // -----------------------------------------------------------------

    private void espacos() {
        while (i < texto.length() && Character.isWhitespace(texto.charAt(i))) i++;
    }

    private Object valor() {
        char c = texto.charAt(i);
        if (c == '{') return objeto();
        if (c == '[') return lista();
        if (c == '"') return cadeia();
        if (texto.startsWith("true", i)) { i += 4; return Boolean.TRUE; }
        if (texto.startsWith("false", i)) { i += 5; return Boolean.FALSE; }
        if (texto.startsWith("null", i)) { i += 4; return null; }
        return numero();
    }

    private Map<String, Object> objeto() {
        Map<String, Object> m = new LinkedHashMap<>();
        i++; // {
        espacos();
        if (texto.charAt(i) == '}') { i++; return m; }
        while (true) {
            espacos();
            String chave = cadeia();
            espacos();
            i++; // :
            espacos();
            m.put(chave, valor());
            espacos();
            char c = texto.charAt(i++);
            if (c == '}') return m;
            if (c != ',') throw new IllegalArgumentException("esperava , ou } na posicao " + i);
        }
    }

    private List<Object> lista() {
        List<Object> l = new ArrayList<>();
        i++; // [
        espacos();
        if (texto.charAt(i) == ']') { i++; return l; }
        while (true) {
            espacos();
            l.add(valor());
            espacos();
            char c = texto.charAt(i++);
            if (c == ']') return l;
            if (c != ',') throw new IllegalArgumentException("esperava , ou ] na posicao " + i);
        }
    }

    private String cadeia() {
        StringBuilder sb = new StringBuilder();
        i++; // "
        while (true) {
            char c = texto.charAt(i++);
            if (c == '"') return sb.toString();
            if (c != '\\') { sb.append(c); continue; }
            char e = texto.charAt(i++);
            switch (e) {
                case 'n': sb.append('\n'); break;
                case 't': sb.append('\t'); break;
                case 'r': sb.append('\r'); break;
                case 'b': sb.append('\b'); break;
                case 'f': sb.append('\f'); break;
                case 'u':
                    sb.append((char) Integer.parseInt(texto.substring(i, i + 4), 16));
                    i += 4;
                    break;
                default: sb.append(e);
            }
        }
    }

    private Double numero() {
        int inicio = i;
        while (i < texto.length() && "+-0123456789.eE".indexOf(texto.charAt(i)) >= 0) i++;
        return Double.valueOf(texto.substring(inicio, i));
    }
}
