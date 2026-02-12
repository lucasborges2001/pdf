# Uso rápido

## 1) Ubicación recomendada

Colocá este repo en:

```
<Materia>/Scripts/_pdf/
```

## 2) Estructura esperada de contenidos

```
<Materia>/
  Practico/XX*/XX*.txt
  Taller/XX*/XX*.txt
  Resumenes/
```

## 3) Build

Desde `<Materia>/Scripts`:

```bash
python -m _pdf.build_all
```

Para opciones ver:

```bash
python -m _pdf.build_all -h
```
