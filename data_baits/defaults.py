K8_NAMESPACE: str = "github-cd"
LOGGER_NAME = "DB"
NAMESPACE_BASE = {
    "apiVersion": "v1",
    "kind": "Namespace",
    "metadata": {
        "name": "",
    },
}
SOURCES_SECRET_BASE = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {
        "name": "",
        "labels": {
            "data-baits-source": "",
            "redeployable-1-name": "sniffer",
            "redeployable-1-namespace": "data-baits",
            "redeployable-1-resource": "job",
        },
    },
    "data": {
        "sources": "",
    },
    "type": "Opaque",
}
KUSTOMIZATION_BASE = {
    "apiVersion": "kustomize.config.k8s.io/v1beta1",
    "kind": "Kustomization",
    "namespace": "data-baits",
    "resources": [],
}
SNIFFER_JOB_BASE = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "name": "",
        "generateName": "",
    },
    "spec": {
        "backoffLimit": 0,
        "template": {
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "image": "ghcr.io/mmazurekgda/data-baits:main",
                        "tty": True,
                        "imagePullPolicy": "Always",
                        "name": "sniffer",
                        "command": [
                            "python",
                            "-m" "data_baits",
                            "--verbosity",
                            "DEBUG",
                            "deploy",
                            "--from_secret",
                        ],
                    },
                ],
                "volumes": [
                    {
                        "name": "volume-kf-pipeline-token",
                        "projected": {
                            "sources": [
                                {
                                    "serviceAccountToken": {
                                        "path": "token",
                                        "expirationSeconds": 7200,
                                        "audience": "pipelines.kubeflow.org",
                                    },
                                },
                            ],
                        },
                    },
                ],
            },
        },
    },
}
