document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const btnMenu = document.getElementById("btnMenu");
    const fondo = document.getElementById("fondoOscuro");

    if (btnMenu) {
        btnMenu.addEventListener("click", function () {
            sidebar.classList.toggle("abierto");
            fondo.classList.toggle("visible");
        });
        fondo.addEventListener("click", function () {
            sidebar.classList.remove("abierto");
            fondo.classList.remove("visible");
        });
    }

    document.querySelectorAll(".mensaje").forEach(function (mensaje) {
        const cerrar = function () {
            mensaje.classList.add("saliendo");
            setTimeout(function () { mensaje.remove(); }, 300);
        };
        mensaje.querySelector(".cerrar-mensaje").addEventListener("click", cerrar);

        if (mensaje.classList.contains("mensaje-exito")) {
            setTimeout(cerrar, 5000);
        }
    });

    const modal = document.getElementById("modalConfirmar");
    let formularioPendiente = null;

    document.addEventListener("submit", function (evento) {
        const form = evento.target;
        if (!form.matches("form[data-confirmar]")) return;
        if (form.dataset.confirmado === "si") return;
        evento.preventDefault();
        formularioPendiente = form;
        document.getElementById("modalTexto").textContent = form.dataset.confirmar;
        modal.hidden = false;
    });

    if (modal) {
        document.getElementById("modalCancelar").addEventListener("click", function () {
            modal.hidden = true;
            formularioPendiente = null;
        });
        document.getElementById("modalAceptar").addEventListener("click", function () {
            if (formularioPendiente) {
                formularioPendiente.dataset.confirmado = "si";
                formularioPendiente.submit();
            }
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") modal.hidden = true;
        });
    }

    document.querySelectorAll("form.js-validar").forEach(function (form) {
        form.setAttribute("novalidate", "");

        const campos = form.querySelectorAll("input, select, textarea");
        campos.forEach(function (campo) {
            campo.addEventListener("blur", function () { validarCampo(campo); });
            campo.addEventListener("input", function () {
                if (campo.closest(".campo") && campo.closest(".campo").classList.contains("invalido")) {
                    validarCampo(campo);
                }
            });
        });

        form.addEventListener("submit", function (evento) {
            let todoBien = true;
            campos.forEach(function (campo) {
                if (!validarCampo(campo)) todoBien = false;
            });
            if (!todoBien) {
                evento.preventDefault();
                const primero = form.querySelector(".invalido input, .invalido select, .invalido textarea");
                if (primero) primero.focus();
            }
        });
    });

    document.querySelectorAll("[data-contar]").forEach(function (elemento) {
        animarNumero(elemento, parseFloat(elemento.dataset.contar));
    });
});

function validarCampo(campo) {
    const caja = campo.closest(".campo");
    if (!caja || campo.type === "hidden" || campo.disabled) return true;

    const valor = campo.value.trim();
    const nombre = caja.querySelector("label") ? caja.querySelector("label").innerText.replace("*", "").trim() : "Este campo";
    let error = "";

    if (campo.required && valor === "") {
        error = nombre + " es obligatorio.";
    } else if (valor !== "") {
        if (campo.minLength > 0 && valor.length < campo.minLength) {
            error = "Debe tener al menos " + campo.minLength + " caracteres.";
        } else if (campo.type === "email" && !/^[\w.+-]+@[\w-]+\.[\w.-]+$/.test(valor)) {
            error = "Escribe un correo válido (ejemplo@colegio.edu.co).";
        } else if (campo.pattern && !new RegExp("^(?:" + campo.pattern + ")$").test(valor)) {
            error = campo.dataset.mensaje || "El formato no es válido.";
        } else if (campo.type === "number") {
            const numero = parseFloat(valor);
            if (campo.min !== "" && numero < parseFloat(campo.min)) error = "El valor mínimo es " + campo.min + ".";
            if (campo.max !== "" && numero > parseFloat(campo.max)) error = "El valor máximo es " + campo.max + ".";
        }
    }

    if (!error && campo.dataset.igualA) {
        const otro = document.getElementById(campo.dataset.igualA);
        if (otro && otro.value !== campo.value) error = "Las contraseñas no coinciden.";
    }

    caja.classList.toggle("invalido", error !== "");
    const texto = caja.querySelector(".error-campo");
    if (texto) texto.textContent = error;
    return error === "";
}

function animarNumero(elemento, final) {
    const decimales = (String(final).split(".")[1] || "").length;
    const sufijo = elemento.dataset.sufijo || "";
    const duracion = 900;
    const inicio = performance.now();

    function paso(ahora) {
        const avance = Math.min((ahora - inicio) / duracion, 1);
        const valor = final * (1 - Math.pow(1 - avance, 3));
        elemento.textContent = valor.toFixed(decimales) + sufijo;
        if (avance < 1) requestAnimationFrame(paso);
    }
    requestAnimationFrame(paso);
}
