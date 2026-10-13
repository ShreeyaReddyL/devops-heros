{{/* Chart name, overridable. */}}
{{- define "campusfix.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Fully qualified release name, used for every resource name. */}}
{{- define "campusfix.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "campusfix.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "campusfix.labels" -}}
helm.sh/chart: {{ include "campusfix.chart" . }}
{{ include "campusfix.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "campusfix.selectorLabels" -}}
app.kubernetes.io/name: {{ include "campusfix.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/* Name of the pre-existing Secret holding the database credentials. */}}
{{- define "campusfix.secretName" -}}
{{- default (printf "%s-postgres" (include "campusfix.fullname" .)) .Values.postgres.existingSecret -}}
{{- end -}}

{{/* Name of the in-cluster PostgreSQL Service. */}}
{{- define "campusfix.postgresFullname" -}}
{{- printf "%s-postgres" (include "campusfix.fullname" .) -}}
{{- end -}}