{{- define "linkpulse.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "linkpulse.labels" -}}
app.kubernetes.io/name: {{ include "linkpulse.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "linkpulse.apiServiceAccountName" -}}
{{- default (printf "%s-api" (include "linkpulse.name" .)) .Values.api.serviceAccountName -}}
{{- end -}}

{{- define "linkpulse.workerServiceAccountName" -}}
{{- default (printf "%s-worker" (include "linkpulse.name" .)) .Values.worker.serviceAccountName -}}
{{- end -}}
