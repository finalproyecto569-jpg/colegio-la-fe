const formNotas = document.getElementById("formNotas");

if (formNotas) {
    const PESOS = { 1: 0.30, 2: 0.30, 3: 0.40 };
    const NOTA_MINIMA = parseFloat(formNotas.dataset.notaMinima);
    let hayCambios = false;

    formNotas.querySelectorAll(".fila-notas").forEach(calcularFila);

    formNotas.addEventListener("input", function (evento) {
        if (!evento.target.classList.contains("input-nota")) return;
        evento.target.value = evento.target.value.replace(",", ".");
        calcularFila(evento.target.closest(".fila-notas"));
        hayCambios = true;
        document.getElementById("avisoCambios").textContent = "Tienes cambios sin guardar";
    });

    formNotas.addEventListener("submit", function (evento) {
        const malas = formNotas.querySelectorAll(".input-nota.mal");
        if (malas.length > 0) {
            evento.preventDefault();
            alert("Hay " + malas.length + " nota(s) inválida(s). Deben ser números entre 0 y 5.");
            malas[0].focus();
            return;
        }
        hayCambios = false;
    });

    window.addEventListener("beforeunload", function (evento) {
        if (hayCambios) {
            evento.preventDefault();
            evento.returnValue = "";
        }
    });

    function notaValida(texto) {
        if (texto === "") return true;
        const numero = Number(texto);
        return !isNaN(numero) && numero >= 0 && numero <= 5;
    }

    function calcularFila(fila) {
        let suma = 0;
        let sumaPesos = 0;
        let error = false;

        fila.querySelectorAll(".input-nota").forEach(function (input) {
            const texto = input.value.trim();
            const valida = notaValida(texto);
            input.classList.toggle("mal", !valida);

            if (!valida) {
                error = true;
            } else if (texto !== "") {
                const nota = Number(texto);
                input.classList.toggle("baja", nota < NOTA_MINIMA);
                suma += nota * PESOS[input.dataset.corte];
                sumaPesos += PESOS[input.dataset.corte];
            } else {
                input.classList.remove("baja");
            }
        });

        const celda = fila.querySelector(".promedio-celda");
        const estado = fila.querySelector(".estado-celda");
        celda.classList.remove("baja", "buena");

        if (error) {
            celda.textContent = "!";
            estado.innerHTML = '<span class="etiqueta nivel-alta">Nota inválida</span>';
        } else if (sumaPesos === 0) {
            celda.textContent = "—";
            estado.innerHTML = '<span class="etiqueta riesgo-sin-datos">Sin notas</span>';
        } else {
            const promedio = suma / sumaPesos;
            celda.textContent = promedio.toFixed(2);
            if (promedio < NOTA_MINIMA) {
                celda.classList.add("baja");
                estado.innerHTML = '<span class="etiqueta nivel-alta">En riesgo</span>';
            } else {
                celda.classList.add("buena");
                estado.innerHTML = '<span class="etiqueta nivel-baja">Aprobando</span>';
            }
        }
    }
}
