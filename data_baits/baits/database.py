from data_baits.bait import Bait
from typing import Optional
from typing_extensions import Literal
from pydantic import model_validator
from kubernetes import client
from data_baits.core.settings import settings
from data_baits.core.storage_class import StorageClass, StorageReclaimPolicy
import logging
import json
import time
import os
import string
import random


class Database(Bait):
    type: Literal["Database"] = "Database"
    namespace: str = settings.K8_NAMESPACE

    def database_name(self) -> str:
        return self.id(use_version=False)

    def id(self, *args, **kwargs) -> str:
        return f"{super().id(*args, **kwargs)}-{self.namespace}"

    def safe_name(self) -> str:
        return self.name.replace("-", "_")


class SQLiteDatabase(Database):
    type: Literal["SQLiteDatabase"] = "SQLiteDatabase"

    def url(self):
        return f"sqlite:///{self.database_name()}.sqlite"

    def deploy(self) -> bool:
        return True

    @staticmethod
    def rollback(*_, **__) -> bool:
        return True


class MySQLInternalDatabase(Database):
    type: Literal["MySQLInternalDatabase"] = "MySQLInternalDatabase"
    port: Optional[int] = 3306
    host: str | None = None
    mount_path: Optional[str] = "/var/lib/mysql"
    storage: Optional[str] = "1Gi"
    # FIXME: this works only with default hostpath provisioner
    # make sure to change it so that it works on S3 too
    storage_class: StorageClass = StorageClass.default
    reclaim_policy: StorageReclaimPolicy = StorageReclaimPolicy.retain
    host_path: str = ""  # will automatically be set to /mnt/{database_name}
    password_env_name: str | None = None
    user_env_name: str | None = None
    connector: Literal[
        "mysql", "mysql+pymysql", "mariadb+pymysql"
    ] = "mysql+pymysql"

    def url(self):
        password = os.environ.get(self.password_env_name)
        if not password:
            raise ValueError(
                f"Password for '{self.database_name()}' not found! "
                "Please make sure that the secret is attached."
            )
        user = os.environ.get(self.user_env_name)
        if not user:
            raise ValueError(
                f"User for '{self.database_name()}' not found! "
                "Please make sure that the secret is attached."
            )
        db = self.database_name().replace("-", "_")
        return (
            f"{self.connector}://{user}:{password}"
            f"@{self.host}:{self.port}/{db}"
        )

    @model_validator(mode="after")
    def fix(self) -> "MySQLInternalDatabase":
        if not self.host_path:
            self.host_path = f"/mnt/{self.database_name()}"
        env_stem = self.database_name().replace("-", "_").upper()
        if self.password_env_name is None:
            self.password_env_name = f"{env_stem}_PASSWORD"
        if self.user_env_name is None:
            self.user_env_name = f"{env_stem}_USER"
        if self.host is None:
            self.host = (
                f"{self.database_name()}.{self.namespace}.svc.cluster.local"
            )
        return self

    def _create_secret(self) -> client.V1Secret:
        # not to be used on production!
        random.seed(self.database_name())
        return client.CoreV1Api().create_namespaced_secret(
            namespace=self.namespace,
            body=client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=self.database_name(),
                    labels={"autogenerated": "true"},
                ),
                string_data={
                    self.password_env_name: "".join(
                        random.choices(
                            string.ascii_letters + string.digits,
                            k=16,
                        )
                    ),
                    self.user_env_name: "root",
                },
            ),
        )

    def _create_deployment(self) -> client.V1Deployment:
        env = [
            client.V1EnvVar(
                name=self.password_env_name,
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=self.database_name(),
                        key=self.password_env_name,
                    )
                ),
            ),
            client.V1EnvVar(
                name=self.user_env_name,
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=self.database_name(),
                        key=self.user_env_name,
                    )
                ),
            ),
        ]
        volumes = [
            client.V1Volume(
                name="mysql-persistent-storage",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(  # noqa
                    claim_name=self.database_name(),
                ),
            )
        ]
        return client.AppsV1Api().create_namespaced_deployment(
            namespace=self.namespace,
            body=client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=self.database_name(),
                    labels={"app": self.database_name()},
                ),
                spec=client.V1DeploymentSpec(
                    selector=client.V1LabelSelector(
                        match_labels={"app": self.database_name()}
                    ),
                    strategy=client.V1DeploymentStrategy(
                        type="Recreate",
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": self.database_name()},
                        ),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    image="mysql:5.6",
                                    name=self.database_name(),
                                    env=env,
                                    ports=[
                                        client.V1ContainerPort(
                                            container_port=self.port,
                                        )
                                    ],
                                    volume_mounts=[
                                        client.V1VolumeMount(
                                            name="mysql-persistent-storage",
                                            mount_path=self.mount_path,
                                        )
                                    ],
                                )
                            ],
                            volumes=volumes,
                        ),
                    ),
                ),
            ),
        )

    def _create_service(self) -> client.V1Service:
        return client.CoreV1Api().create_namespaced_service(
            namespace=self.namespace,
            body=client.V1Service(
                metadata=client.V1ObjectMeta(
                    name=self.database_name(),
                    labels={"app": self.database_name()},
                ),
                spec=client.V1ServiceSpec(
                    selector={"app": self.database_name()},
                    ports=[
                        client.V1ServicePort(
                            port=self.port,
                        )
                    ],
                ),
            ),
        )

    def _create_persistent_volume(self) -> client.V1PersistentVolume:
        return client.CoreV1Api().create_persistent_volume(
            body=client.V1PersistentVolume(
                metadata=client.V1ObjectMeta(
                    name=self.database_name(),
                    labels={"type": "local"},
                ),
                spec=client.V1PersistentVolumeSpec(
                    persistent_volume_reclaim_policy=self.reclaim_policy,
                    storage_class_name=self.storage_class,
                    capacity={"storage": self.storage},
                    access_modes=["ReadWriteOnce"],
                    host_path=client.V1HostPathVolumeSource(
                        path=self.host_path,
                    ),
                ),
            ),
        )

    def _create_persistent_volume_claim(
        self,
    ) -> client.V1PersistentVolumeClaim:
        return client.CoreV1Api().create_namespaced_persistent_volume_claim(
            namespace=self.namespace,
            body=client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(
                    name=self.database_name(),
                ),
                spec=client.V1PersistentVolumeClaimSpec(
                    storage_class_name=self.storage_class,
                    access_modes=["ReadWriteOnce"],
                    resources=client.V1ResourceRequirements(
                        requests={"storage": self.storage}
                    ),
                ),
            ),
        )

    def deploy(self) -> bool:
        logger = logging.getLogger(settings.LOGGER_NAME)
        passed = True
        try:
            logger.debug(
                f"-> Checking if secret {self.database_name()} exists..."
            )
            client.CoreV1Api().read_namespaced_secret(
                name=self.database_name(),
                namespace=self.namespace,
            )
        except client.exceptions.ApiException:
            logger.warning(
                f"-> Secret {self.database_name()} not found! "
                "Will create a new one. This cannot be used on production!"
            )
            self._create_secret()
        for resource_name, deploy_resource in [
            ("deployment", self._create_deployment),
            ("service", self._create_service),
            ("persistent_volume", self._create_persistent_volume),
            ("persistent_volume_claim", self._create_persistent_volume_claim),
        ]:
            try:
                logger.debug(f"-> Creating {resource_name}...")
                deploy_resource()
            except client.exceptions.ApiException as e:
                logger.error(
                    f"-> {resource_name} creation failed! " f"Details:\n{e}"
                )
                if json.loads(e.body).get("reason", "") != "AlreadyExists":
                    passed = False
        return passed

    @staticmethod
    def rollback(
        name: str,  # eq. of database_name()
        namespace: str,
    ) -> bool:
        logger = logging.getLogger(settings.LOGGER_NAME)
        v1 = client.CoreV1Api()
        v1_apps = client.AppsV1Api()
        passed = True
        try:
            logger.debug(f"-> Deleting auto generated secrets {name}...")
            secret = v1.read_namespaced_secret(
                name=name,
                namespace=namespace,
            )
            if secret.metadata.labels.get("autogenerated", "") == "true":
                v1.delete_namespaced_secret(
                    name=name,
                    namespace=namespace,
                )
        except client.exceptions.ApiException as e:
            if json.loads(e.body).get("reason", "") != "NotFound":
                logger.debug(
                    f"-> {name} secret deletion failed! Details:\n{e}"
                )
                passed = False
            else:
                logger.debug("-> No autogenerated secrets found.")
        for resource_name, callback in [
            ("service", v1.delete_namespaced_service),
            ("deployment", v1_apps.delete_namespaced_deployment),
            (
                "persistent_volume_claim",
                v1.delete_namespaced_persistent_volume_claim,
            ),
            ("persistent_volume", v1.delete_persistent_volume),
        ]:
            try:
                logger.debug(f"-> Deleting {resource_name}...")
                kwargs = {
                    "name": name,
                }
                if resource_name != "persistent_volume":
                    kwargs["namespace"] = namespace
                callback(**kwargs)
                # sleep just in case to propagate the changes
                time.sleep(3)
            except client.exceptions.ApiException as e:
                logger.error(
                    f"-> {resource_name} deletion failed! " f"Details:\n{e}"
                )
                if json.loads(e.body).get("reason", "") != "NotFound":
                    passed = False
        return passed
