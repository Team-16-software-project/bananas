#include <bananas_aruco/visualization/visualizer.h>

#include <Eigen/Core>
#include <Eigen/Geometry>

#include <gsl/assert>
#include <gsl/pointers>

#include <OgreApplicationContext.h>
#include <OgreCamera.h>
#include <OgreCameraMan.h>
#include <OgreEntity.h>
#include <OgreInput.h>
#include <OgreLight.h>
#include <OgreMath.h>
#include <OgreNode.h>
#include <OgrePrerequisites.h>
#include <OgreQuaternion.h>
#include <OgreRenderWindow.h>
#include <OgreRoot.h>
#include <OgreSceneManager.h>
#include <OgreShaderGenerator.h>

#include <bananas_aruco/affine_rotation.h>
#include <bananas_aruco/box_board.h>
#include <bananas_aruco/grid_board.h>
#include <bananas_aruco/world.h>

namespace {

void set_transform(Ogre::SceneNode *node,
                   const affine_rotation::AffineRotation &transform) {
    node->setPosition(Ogre::Vector3f{transform.getTranslation().data()});

    const auto rotation{transform.getRotation()};
    node->setOrientation(Ogre::Quaternion{rotation.w(), rotation.x(),
                                          rotation.y(), rotation.z()});
}

} // namespace

namespace visualizer {

Visualizer::KeyHandler::KeyHandler(OgreBites::CameraMan *camera_manager)
    : camera_manager_{camera_manager} {}

auto Visualizer::KeyHandler::mousePressed(
    const OgreBites::MouseButtonEvent & /*evt*/) -> bool {
    camera_manager_->setStyle(OgreBites::CameraStyle::CS_FREELOOK);
    return true;
}

auto Visualizer::KeyHandler::mouseReleased(
    const OgreBites::MouseButtonEvent & /*evt*/) -> bool {
    camera_manager_->setStyle(OgreBites::CameraStyle::CS_MANUAL);
    return true;
}

Visualizer::InitializedContext::InitializedContext()
    : OgreBites::ApplicationContext{} {
    initApp();
}

Visualizer::Visualizer()
    : root_{context_.getRoot()}, scene_manager_{root_->createSceneManager()},
      camera_node_{scene_manager_->getRootSceneNode()->createChildSceneNode()},
      camera_manager_{camera_node_}, key_handler_{&camera_manager_},
      static_environment_{
          scene_manager_->getRootSceneNode()->createChildSceneNode()},
      camera_visualization_{
          scene_manager_->getRootSceneNode()->createChildSceneNode()} {
    const gsl::not_null<Ogre::RTShader::ShaderGenerator *> shadergen{
        Ogre::RTShader::ShaderGenerator::getSingletonPtr()};
    shadergen->addSceneManager(scene_manager_);

    const gsl::not_null<Ogre::Light *> light{
        scene_manager_->createLight("light")};
    const gsl::not_null<Ogre::SceneNode *> lightNode{
        scene_manager_->getRootSceneNode()->createChildSceneNode()};
    lightNode->setPosition(10, 15, 10);
    lightNode->attachObject(light);

    camera_node_->setPosition(2, 1, 2);
    camera_node_->lookAt(Ogre::Vector3{0, 0, 0}, Ogre::Node::TS_PARENT);

    const gsl::not_null<Ogre::Camera *> camera{
        scene_manager_->createCamera("camera")};
    camera->setNearClipDistance(0.1);
    camera->setAutoAspectRatio(true);
    camera_node_->attachObject(camera);

    camera_manager_.setStyle(OgreBites::CameraStyle::CS_MANUAL);
    camera_manager_.setTopSpeed(2.0F);

    context_.getRenderWindow()->addViewport(camera);

    context_.addInputListener(&key_handler_);
    context_.addInputListener(&camera_manager_);

    const gsl::not_null<Ogre::Entity *> camera_visualization_entity{
        scene_manager_->createEntity(Ogre::SceneManager::PT_CUBE)};
    camera_visualization_->setScale(0.00025F, 0.00025F, 0.00125F);
    camera_visualization_->attachObject(camera_visualization_entity);
    camera_visualization_->setVisible(false);
}

void Visualizer::update(world::BoardId id,
                        const affine_rotation::AffineRotation &placement) {
    set_transform(objects_.at(id), placement);
}

void Visualizer::update(const world::FitResult &fit) {
    camera_visualization_->setVisible(fit.camera_to_world.has_value());
    if (fit.camera_to_world) {
        set_transform(camera_visualization_, *fit.camera_to_world);
    }
    for (const auto &[id, node] : objects_) {
        const auto object_placement{fit.dynamic_board_placements.find(id)};
        const bool has_placement{object_placement !=
                                 fit.dynamic_board_placements.cend()};
        if (forced_visible_.find(id) == forced_visible_.end()) {
            node->setVisible(has_placement);
        }
        if (has_placement) {
            set_transform(node, object_placement->second);
        }
    }
}

void Visualizer::refresh() { context_.getRoot()->renderOneFrame(); }

void Visualizer::addObject(world::BoardId id, const board::BoxSettings &box) {
    const gsl::not_null<Ogre::Entity *> cube{
        scene_manager_->createEntity(Ogre::SceneManager::PT_CUBE)};
    const gsl::not_null<Ogre::SceneNode *> node{
        scene_manager_->getRootSceneNode()->createChildSceneNode()};

    node->setScale({0.01F * box.size.width, 0.01F * box.size.height,
                    0.01F * box.size.depth});
    node->attachObject(cube);
    node->setVisible(false);

    objects_.emplace(id, node);
}

void Visualizer::addObject(world::BoardId id, const board::GridSettings &grid) {
    const gsl::not_null<Ogre::Entity *> plane{
        scene_manager_->createEntity(Ogre::SceneManager::PT_PLANE)};
    const gsl::not_null<Ogre::SceneNode *> node{
        scene_manager_->getRootSceneNode()->createChildSceneNode()};

    // Make the plane point up (+Y direction) by default.
    const gsl::not_null<Ogre::SceneNode *> child_node{
        node->createChildSceneNode(
            Ogre::Vector3{0.0F, 0.0F, 0.0F},
            Ogre::Quaternion{Ogre::Degree{270}, Ogre::Vector3{1, 0, 0}})};
    child_node->attachObject(plane);
    node->setVisible(false);

    node->setScale(0.005F * board::grid_width(grid),
                   0.005F * board::grid_height(grid), 1.0F);

    objects_.emplace(id, node);
}

void Visualizer::forceVisible(world::BoardId id) {
    const auto location{objects_.find(id)};
    Expects(location != objects_.cend());

    location->second->setVisible(true);
    forced_visible_.insert(id);
}

} // namespace visualizer
