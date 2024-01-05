K8_NAMESPACE: str = "github-cd"
LOGGER_NAME = "DB"
CONFIG_MAP_BASE = {
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {
        "name": "data-baits-sources",
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
}
KUSTOMIZATION_BASE = {
    "apiVersion": "kustomize.config.k8s.io/v1beta1",
    "kind": "Kustomization",
    "resources": [
        "config_map.yaml",
    ],
}
SNIFFER_JOB_BASE = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {
        "name": "sniffer",
    },
    "spec": {
        "backoffLimit": 0,
        "template": {
            "spec": {
                "containers": [
                    {
                        "image": "ghcr.io/mmazurekgda/data-baits:main",
                        "tty": True,
                        "imagePullPolicy": "Always",
                        "name": "sniffer",
                        "command": [
                            "python",
                            "/code/app/main.py",
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
